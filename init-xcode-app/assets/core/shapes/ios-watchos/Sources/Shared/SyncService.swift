import Foundation

public final class SyncService: ObservableObject {
    @Published public private(set) var items: [Item]
    public init(items: [Item] = Item.samples) { self.items = items }
    public func reload() { items = Item.samples }
}
