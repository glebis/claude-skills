import SwiftUI
import <Name>SharedWatch

struct WatchContentView: View {
    @EnvironmentObject private var sync: SyncService
    var body: some View {
        List(sync.items) { Text($0.title) }
    }
}
