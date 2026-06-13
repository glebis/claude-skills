import Foundation

struct Item: Identifiable, Codable, Hashable {
    let id: UUID
    let title: String
    let detail: String

    init(id: UUID = UUID(), title: String, detail: String) {
        self.id = id
        self.title = title
        self.detail = detail
    }

    static let samples = [
        Item(title: "First", detail: "A sample item."),
        Item(title: "Second", detail: "Another sample item."),
    ]
}
