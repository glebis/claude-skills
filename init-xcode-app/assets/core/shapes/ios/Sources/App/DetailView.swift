import SwiftUI

struct DetailView: View {
    let item: Item
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(item.title).font(.title)
            Text(item.detail).foregroundStyle(.secondary)
            Spacer()
        }
        .padding()
        .navigationTitle(item.title)
    }
}
