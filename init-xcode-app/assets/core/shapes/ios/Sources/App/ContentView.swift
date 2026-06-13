import SwiftUI

struct ContentView: View {
    private let items = Item.samples
    var body: some View {
        NavigationStack {
            List(items) { item in
                NavigationLink(item.title) { DetailView(item: item) }
            }
            .navigationTitle("<Name>")
        }
    }
}
