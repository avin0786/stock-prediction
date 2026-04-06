import pandas as pd

class ZerodhaOptionChain:
    def __init__(self, kite):
        self.kite = kite
        self.instruments_df = None

    # ✅ Step 1: Load all instruments once (cache this)
    def load_instruments(self):
        instruments = self.kite.instruments("NFO")
        self.instruments_df = pd.DataFrame(instruments)

    # ✅ Step 2: Get NIFTY option contracts
    def get_nifty_options(self):
        df = self.instruments_df

        nifty_df = df[
            (df['name'] == 'NIFTY') &
            (df['segment'] == 'NFO-OPT')
        ].copy()

        nifty_df['expiry'] = pd.to_datetime(nifty_df['expiry'])

        return nifty_df

    # ✅ Step 3: Get nearest expiry
    def get_nearest_expiry(self, nifty_df):
        return sorted(nifty_df['expiry'].unique())[0]

    # ✅ Step 4: Get current option chain
    def get_option_chain(self):

        nifty_df = self.get_nifty_options()

        nearest_expiry = self.get_nearest_expiry(nifty_df)

        current_options = nifty_df[
            nifty_df['expiry'] == nearest_expiry
        ]

        tokens = current_options['instrument_token'].tolist()

        # ⚠️ Zerodha limit ~500 instruments per call
        chunks = [tokens[i:i+400] for i in range(0, len(tokens), 400)]

        all_quotes = {}

        for chunk in chunks:
            quotes = self.kite.quote(chunk)
            all_quotes.update(quotes)

        # Merge data
        records = []

        for _, row in current_options.iterrows():
            token = row['instrument_token']

            if token in all_quotes:
                q = all_quotes[token]

                records.append({
                    "tradingsymbol": row['tradingsymbol'],
                    "strike": row['strike'],
                    "type": row['instrument_type'],  # CE / PE
                    "expiry": row['expiry'],
                    "ltp": q['last_price'],
                    "oi": q.get('oi', 0),
                    "volume": q.get('volume', 0),
                    "bid": q['depth']['buy'][0]['price'] if q['depth']['buy'] else None,
                    "ask": q['depth']['sell'][0]['price'] if q['depth']['sell'] else None,
                })

        return pd.DataFrame(records)