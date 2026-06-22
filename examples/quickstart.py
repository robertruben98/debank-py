"""Synchronous quickstart for debank-py.

Run with a real, paid DeBank Cloud AccessKey:

    DEBANK_ACCESS_KEY=your-key python examples/quickstart.py
"""

import os

from debank import DeBankClient

WALLET = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # any wallet address


def main() -> None:
    access_key = os.environ["DEBANK_ACCESS_KEY"]  # required (paid)
    with DeBankClient(access_key=access_key) as client:
        total = client.get_user_total_balance(id=WALLET)
        print(f"Total net worth: ${total.total_usd_value:,.2f}")
        for chain in total.chain_list:
            print(f"  {chain.name or chain.id}: ${chain.usd_value:,.2f}")

        print("\nTop token holdings:")
        tokens = client.get_user_all_token_list(id=WALLET)
        for token in sorted(tokens, key=lambda t: (t.amount or 0) * (t.price or 0), reverse=True)[
            :10
        ]:
            print(f"  {token.chain}:{token.symbol} amount={token.amount}")


if __name__ == "__main__":
    main()
