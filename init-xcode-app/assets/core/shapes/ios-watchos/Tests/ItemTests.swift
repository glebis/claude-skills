import Testing
@testable import <Name>Shared

struct ItemTests {
    @Test func samplesArePresent() {
        #expect(Item.samples.count == 2)
        #expect(Item.samples.first?.title == "First")
    }
}
