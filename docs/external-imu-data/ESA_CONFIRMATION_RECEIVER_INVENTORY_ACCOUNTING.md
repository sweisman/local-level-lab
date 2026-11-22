# Receiver-only screen with corrected work accounting

The first inventory closed with eight technical failures. The worker required
both a call count and a step count in each reservation, and the adapter passed
only one. All eight starts remain in the first ledger. Zero decoding or
selection operations were charged, and no receiver or model outcome was scored.
[First run ledger](esa-confirmation-receiver-inventory-result.json)

The separate version-2 inventory keeps the same [scope, thresholds and files](ESA_CONFIRMATION_RECEIVER_INVENTORY_PLAN.md).
Each task allows at most 100,001 decoder steps, reserved in blocks of up to
1,024, followed by one selection. Each block and the selection are charged
as complete operations before execution. There is one task per file, one
thread and a 300-second cooperative wall cap. Test the operation contract
on a generated receiver export before launching. Keep the same qualified
technical recovery policy. No inertial data, protected model outcomes or
Earth-model fits enter the inventory.
