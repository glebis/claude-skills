use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct PingRequest { pub message: String }

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct PingResponse { pub reply: String }

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn roundtrip() {
        let r = PingRequest { message: "hi".into() };
        let s = serde_json::to_string(&r).unwrap();
        let back: PingRequest = serde_json::from_str(&s).unwrap();
        assert_eq!(back.message, "hi");
    }
}
