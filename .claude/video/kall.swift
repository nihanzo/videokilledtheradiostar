import AVFoundation
import AppKit
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let asset = AVURLAsset(url: url)
let reader = try! AVAssetReader(asset: asset)
let track = asset.tracks(withMediaType: .video)[0]
let out = AVAssetReaderTrackOutput(track: track, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
reader.add(out); reader.startReading()
var i = 0
let ctx = CIContext()
while let sb = out.copyNextSampleBuffer() {
  guard let pb = CMSampleBufferGetImageBuffer(sb) else { continue }
  let ci = CIImage(cvPixelBuffer: pb)
  let cg = ctx.createCGImage(ci, from: ci.extent)!
  let data = NSBitmapImageRep(cgImage: cg).representation(using: .png, properties: [:])!
  try! data.write(to: URL(fileURLWithPath: String(format: "kall/a%03d.png", i)))
  i += 1
}
print("frames", i)
