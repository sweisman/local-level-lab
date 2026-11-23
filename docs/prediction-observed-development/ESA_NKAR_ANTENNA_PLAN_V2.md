# Verify the antenna replay with the orbit reader’s position type

Apply the original [antenna replay plan](ESA_NKAR_ANTENNA_PLAN.md) with its
same inputs, correction terms, score and one-task allowance. The first run
stopped on the first aircraft pair with a Python `TypeError`. It charged
one setup and one pair, produced no result, and remains terminal. Its
manifest hash is
`878367d1d19375ea0cd761d4528fc03a0dcb60e0c3d2e38649378d1125610a09`.

Move the orientation check into the correction function, which accepts
the position tuple returned by the orbit reader and converts it to an
array. Test the tuple case and verify that the orientation check still
rejects a satellite pointing away from its declared body axis. Keep all
other conventions and bounds. Use a new qualification, freeze and receipt.
