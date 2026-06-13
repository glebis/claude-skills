// macOS-only FFI to the AppSidecar Swift static lib.
#[cfg(target_os = "macos")]
mod ffi {
    use std::ffi::{CStr, CString};
    use std::os::raw::c_char;
    extern "C" {
        fn app_sidecar_greet(name: *const c_char) -> *mut c_char;
        fn app_sidecar_free(p: *mut c_char);
    }
    pub fn greet(name: &str) -> String {
        let c = CString::new(name).unwrap_or_default();
        unsafe {
            let p = app_sidecar_greet(c.as_ptr());
            if p.is_null() { return String::new(); }
            let s = CStr::from_ptr(p).to_string_lossy().into_owned();
            app_sidecar_free(p);
            s
        }
    }
}
#[cfg(target_os = "macos")]
pub use ffi::greet;
