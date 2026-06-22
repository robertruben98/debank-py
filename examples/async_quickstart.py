"""Asynchronous quickstart for debank-py.

Run with a real, paid DeBank Cloud AccessKey:

    DEBANK_ACCESS_KEY=your-key python examples/async_quickstart.py
"""

import asyncio
import os

from debank import AsyncDeBankClient

WALLET = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


async def main() -> None:
    access_key = os.environ["DEBANK_ACCESS_KEY"]  # required (paid)
    async with AsyncDeBankClient(access_key=access_key) as client:
        total, protocols = await asyncio.gather(
            client.get_user_total_balance(id=WALLET),
            client.get_user_all_complex_protocol_list(id=WALLET),
        )
        print(f"Total net worth: ${total.total_usd_value:,.2f}")
        print(f"Open DeFi protocols: {len(protocols)}")
        for protocol in protocols[:10]:
            print(f"  {protocol.chain}:{protocol.name}")


if __name__ == "__main__":
    asyncio.run(main())
