import SwiftUI
import <Name>Shared

@main
struct <Name>App: App {
    @StateObject private var sync = SyncService()
    var body: some Scene {
        WindowGroup { ContentView().environmentObject(sync) }
    }
}
