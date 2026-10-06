// Zusammenhangskomponenten (8er-Nachbarschaft, Union-Find) einer 8-bit-Rohmaske; Flächen < amin werden gelöscht.
// Aufruf: ccfilter <in.raw> <W> <H> <amin> <out.raw>   (Pixel > 127 = Vordergrund)
import Foundation
let a = CommandLine.arguments
let W = Int(a[2])!, H = Int(a[3])!, amin = Int(a[4])!
var px = [UInt8](try! Data(contentsOf: URL(fileURLWithPath: a[1])))
var lab = [Int32](repeating: 0, count: W*H)
var parent: [Int32] = [0]
func find(_ x: Int32) -> Int32 { var r = x; while parent[Int(r)] != r { r = parent[Int(r)] }
  var c = x; while parent[Int(c)] != r { let n = parent[Int(c)]; parent[Int(c)] = r; c = n }; return r }
func unite(_ x: Int32, _ y: Int32) { let rx = find(x), ry = find(y); if rx != ry { if rx < ry { parent[Int(ry)] = rx } else { parent[Int(rx)] = ry } } }
for y in 0..<H { for x in 0..<W {
  let i = y*W + x; if px[i] <= 127 { continue }
  var best: Int32 = 0
  for (dx, dy) in [(-1, 0), (-1, -1), (0, -1), (1, -1)] {
    let nx = x + dx, ny = y + dy; if nx < 0 || ny < 0 || nx >= W { continue }
    let l = lab[ny*W + nx]; if l == 0 { continue }
    if best == 0 { best = l } else { unite(best, l); best = min(best, l) }
  }
  if best == 0 { best = Int32(parent.count); parent.append(best) }
  lab[i] = best
} }
var area = [Int](repeating: 0, count: parent.count)
for i in 0..<W*H where lab[i] != 0 { let r = find(lab[i]); lab[i] = r; area[Int(r)] += 1 }
var small = 0, big = 0
for (k, v) in area.enumerated() where k > 0 && parent[k] == Int32(k) && v > 0 { if v < amin { small += 1 } else { big += 1 } }
for i in 0..<W*H { px[i] = (lab[i] != 0 && area[Int(lab[i])] >= amin) ? 255 : 0 }
try! Data(px).write(to: URL(fileURLWithPath: a[5]))
print("big \(big) small \(small)")
