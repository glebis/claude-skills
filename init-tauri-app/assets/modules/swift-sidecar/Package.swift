// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "AppSidecar",
    platforms: [.macOS(.v13)],
    products: [
        .library(name: "AppSidecar", type: .static, targets: ["AppSidecar"]),
    ],
    targets: [
        .target(name: "AppSidecar", linkerSettings: [
            .linkedFramework("Foundation"),
        ]),
    ]
)
