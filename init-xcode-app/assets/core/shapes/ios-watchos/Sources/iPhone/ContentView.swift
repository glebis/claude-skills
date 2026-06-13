import SwiftUI
import <Name>Shared

struct ContentView: View {
    @EnvironmentObject private var sync: SyncService
    var body: some View {
        NavigationStack {
            List(sync.items) { item in
                VStack(alignment: .leading) {
                    Text(item.title).font(.headline)
                    Text(item.detail).font(.subheadline).foregroundStyle(.secondary)
                }
            }
            .navigationTitle("<Name>")
        }
    }
}
