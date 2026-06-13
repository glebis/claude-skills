import Foundation

// Kind tags — KEEP IN SYNC with the Rust side (see sidecar_ffi.rs).
// 0 = OK, 1 = ERROR

@_cdecl("app_sidecar_greet")
public func app_sidecar_greet(_ name: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>? {
    let who = name.flatMap { String(validatingUTF8: $0) } ?? "world"
    return strdup("hello, \(who)")
}

@_cdecl("app_sidecar_free")
public func app_sidecar_free(_ p: UnsafeMutablePointer<CChar>?) {
    if let p { free(p) }
}
