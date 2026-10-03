# Data handling and access: demonstration policy

All data in this repository are fictional. This example is not a GDPR approval, a security certification, or authorization to process real research data.

## Example data flow

1. Keep an untouched source export in a restricted raw-data location.
2. Record its checksum and version, then make cleaning changes only through code.
3. Keep cleaned analysis files separate from the source and retain a processing log.
4. If a participant identifier must be retained, store any re-linkage key separately with narrower access and an approved retention period.
5. Delete or archive data only under the study's approved plan and institutional rules.

Replacing a direct ID with a code such as `Sub_001` is pseudonymisation if another file or party can reconnect the code to a person. It should not be called anonymisation in that case. The demo uses `SYN-001` values that have no identity mapping.

## Example least-privilege roles

| Role | Example access |
|---|---|
| Principal investigator | Study protocol and approved results; raw-data access only if required |
| Data manager | Restricted raw export and linkage key, if needed for the approved task |
| Analyst | Pseudonymised/derived analysis data; no linkage key by default |
| External collaborator | Only the approved, minimum dataset under the data-sharing agreement |

## API key and budget routine

- Use a separate credential per project or service where the provider supports it; do not share one person's key with a whole lab.
- Store secrets in an approved secret manager or protected environment variables, not in Git.
- Give access only to named maintainers; review access when a project or role ends.
- Set provider-side spending alerts or limits where available, review usage, and rotate/revoke credentials when needed.
- The batch example uses a local estimated budget to stop before starting another simulated request. It is a teaching guard, not a provider-enforced financial cap.

For real NTNU research, confirm platform, storage location, access approvals, retention, consent, and data-protection requirements with the relevant institutional data-protection and research-support functions before collecting data.
