// Grünkohl hochskalieren mit Apples KI-Hochskalierung (VideoToolbox VTSuperResolutionScaler, macOS 26+, nur Faktor 4,
// Eingabe max. 1920×1080), danach Lanczos auf die Zielgröße. Bilder werden als Video-Folge verarbeitet (Vorbild +
// voriges Ergebnis -> zeitlich ruhig). Aufruf: swift sr4.swift <Eingabe-Ordner> <Ausgabe-Ordner> <Breite> <Höhe>
import VideoToolbox
import CoreImage
import Foundation
func log(_ x: Any...) { FileHandle.standardError.write((x.map { "\($0)" }.joined(separator: " ") + "\n").data(using: .utf8)!) }

@available(macOS 26.0, *)
func run() async throws {
  let a = CommandLine.arguments, inDir = a[1], outDir = a[2], OW = Double(a[3])!, OH = Double(a[4])!
  let files = try FileManager.default.contentsOfDirectory(atPath: inDir).filter { $0.hasSuffix(".png") }.sorted()
  try? FileManager.default.createDirectory(atPath: outDir, withIntermediateDirectories: true)
  let first = CIImage(contentsOf: URL(fileURLWithPath: inDir + "/" + files[0]))!
  let W = Int(first.extent.width), H = Int(first.extent.height)
  guard let cfg = VTSuperResolutionScalerConfiguration(frameWidth: W, frameHeight: H, scaleFactor: 4, inputType: .video,
      usePrecomputedFlow: false, qualityPrioritization: .normal, revision: VTSuperResolutionScalerConfiguration.defaultRevision)
  else { print("Konfiguration nicht möglich für", W, H); return }
  if cfg.configurationModelStatus != .ready {
    log("Modell-Status", cfg.configurationModelStatus.rawValue, "-> wird geladen …"); try await cfg.downloadConfigurationModel(); log("Modell-Status jetzt", cfg.configurationModelStatus.rawValue)
  }
  log("Status", cfg.configurationModelStatus.rawValue, "Start Sitzung"); let proc = VTFrameProcessor(); try proc.startSession(configuration: cfg); log("Sitzung läuft")
  let srgb = CGColorSpace(name: CGColorSpace.sRGB)!
  let ctx = CIContext(options: [.workingColorSpace: srgb, .outputColorSpace: srgb])
  func buffer(_ w: Int, _ h: Int) -> CVPixelBuffer {
    var pb: CVPixelBuffer?
    CVPixelBufferCreate(nil, w, h, kCVPixelFormatType_64RGBAHalf, [kCVPixelBufferIOSurfacePropertiesKey: [:]] as CFDictionary, &pb)
    return pb!
  }
  var prevS: VTFrameProcessorFrame? = nil, prevD: VTFrameProcessorFrame? = nil
  for (i, f) in files.enumerated() {
    let img = CIImage(contentsOf: URL(fileURLWithPath: inDir + "/" + f))!
    let src = buffer(W, H); ctx.render(img, to: src, bounds: img.extent, colorSpace: srgb)
    let dst = buffer(W*4, H*4)
    let pts = CMTime(value: CMTimeValue(i), timescale: 24)
    let sf = VTFrameProcessorFrame(buffer: src, presentationTimeStamp: pts)!, df = VTFrameProcessorFrame(buffer: dst, presentationTimeStamp: pts)!
    let p = VTSuperResolutionScalerParameters(sourceFrame: sf, previousFrame: prevS, previousOutputFrame: prevD, opticalFlow: nil,
                                              submissionMode: prevS == nil ? .random : .sequential, destinationFrame: df)!
    try await proc.process(parameters: p)
    prevS = sf; prevD = df
    if i == 0 {
      func stats(_ pb: CVPixelBuffer, _ name: String) {
        CVPixelBufferLockBaseAddress(pb, .readOnly); defer { CVPixelBufferUnlockBaseAddress(pb, .readOnly) }
        let w = CVPixelBufferGetWidth(pb), h = CVPixelBufferGetHeight(pb), bpr = CVPixelBufferGetBytesPerRow(pb)
        let base = CVPixelBufferGetBaseAddress(pb)!
        var mn: Float = 1e9, mx: Float = -1e9, sum: Double = 0, n = 0
        for y in stride(from: 0, to: h, by: 7) { let row = (base + y*bpr).assumingMemoryBound(to: Float16.self)
          for x in stride(from: 0, to: w, by: 7) { for c in 0..<3 { let v = Float(row[x*4+c]); mn = min(mn, v); mx = max(mx, v); sum += Double(v); n += 1 } } }
        log(name, w, h, "fmt", CVPixelBufferGetPixelFormatType(pb), "min", mn, "max", mx, "mean", sum/Double(n))
      }
      stats(src, "src"); stats(dst, "dst")
    }
    let big0 = CIImage(cvPixelBuffer: dst, options: [.colorSpace: srgb])
    let big = big0.settingAlphaOne(in: big0.extent)              // Modell schreibt keinen Alpha-Kanal -> deckend
    let sy = OH/Double(H*4), sx = OW/Double(W*4)
    let small = big.applyingFilter("CILanczosScaleTransform", parameters: ["inputScale": sy, "inputAspectRatio": sx/sy])
      .cropped(to: CGRect(x: 0, y: 0, width: OW, height: OH))
    try ctx.writePNGRepresentation(of: small, to: URL(fileURLWithPath: outDir + "/" + f), format: .RGBA8, colorSpace: srgb)
    if i % 10 == 0 { print(i, "/", files.count) }
  }
  proc.endSession(); print("fertig", files.count, Int(OW), Int(OH))
}
@main struct SR4 { static func main() async throws { if #available(macOS 26.0, *) { try await run() } else { print("braucht macOS 26") } } }
