// Apple Vision: Vordergrund-Maske (dasselbe Modell wie „Hintergrund entfernen“ in Vorschau/Finder) als Graustufen-PNG
import Vision
import CoreImage
import AppKit
let inURL = URL(fileURLWithPath: CommandLine.arguments[1]), outPath = CommandLine.arguments[2]
let ci = CIImage(contentsOf: inURL)!
let handler = VNImageRequestHandler(ciImage: ci)
let req = VNGenerateForegroundInstanceMaskRequest()
try! handler.perform([req])
guard let obs = req.results?.first else { print("no foreground"); exit(1) }
let pb = try! obs.generateScaledMaskForImage(forInstances: obs.allInstances, from: handler)
let mask = CIImage(cvPixelBuffer: pb)
let ctx = CIContext()
let cg = ctx.createCGImage(mask, from: mask.extent, format: .L8, colorSpace: CGColorSpaceCreateDeviceGray())!
try! NSBitmapImageRep(cgImage: cg).representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: outPath))
print("instances", obs.allInstances.count, "mask", cg.width, cg.height)
