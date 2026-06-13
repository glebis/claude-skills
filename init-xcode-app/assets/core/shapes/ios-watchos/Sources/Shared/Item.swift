import Foundation

public struct Item: Identifiable, Codable, Hashable {
    public let id: UUID
    public let title: String
    public let detail: String

    public init(id: UUID = UUID(), title: String, detail: String) {
        self.id = id
        self.title = title
        self.detail = detail
    }

    public static let samples = [
        Item(title: "First", detail: "A sample item."),
        Item(title: "Second", detail: "Another sample item."),
    ]
}
