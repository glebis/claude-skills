use tauri::{AppHandle, Manager};
use tauri::tray::TrayIconBuilder;
use tauri::menu::{Menu, MenuItem};

pub fn build(app: &AppHandle) -> tauri::Result<()> {
    let show = MenuItem::with_id(app, "show", "Show", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&show, &quit])?;
    TrayIconBuilder::new()
        .menu(&menu)
        .on_menu_event(|app, event| match event.id.as_ref() {
            "show" => { if let Some(w) = app.get_webview_window("main") { let _ = w.show(); let _ = w.set_focus(); } }
            "quit" => app.exit(0),
            _ => {}
        })
        .build(app)?;
    Ok(())
}
