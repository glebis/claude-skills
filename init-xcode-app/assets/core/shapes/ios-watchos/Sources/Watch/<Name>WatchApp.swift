import SwiftUI
import <Name>SharedWatch

@main
struct <Name>WatchApp: App {
    @StateObject private var sync = SyncService()
    var body: some Scene {
        WindowGroup { WatchContentView().environmentObject(sync) }
    }
}
