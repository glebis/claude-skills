import CloudKit
import Foundation

/// Minimal CloudKit store stub. Container id must match the entitlement.
public final class CloudKitStore {
    private let container: CKContainer
    public init(identifier: String = "iCloud.<bundlePrefix>.<name>") {
        self.container = CKContainer(identifier: identifier)
    }
    /// Fetches the account status; expand with record fetch/save as needed.
    public func accountStatus() async throws -> CKAccountStatus {
        try await container.accountStatus()
    }
}
