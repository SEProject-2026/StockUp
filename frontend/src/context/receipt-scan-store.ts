// frontend/src/state/receipt-scan-store.ts
let _lastReceipt: any | null = null;

export function setLastScannedReceipt(receipt: any) {
  _lastReceipt = receipt ?? null;
}

export function getLastScannedReceipt() {
  return _lastReceipt;
}

export function consumeLastScannedReceipt() {
  const r = _lastReceipt;
  _lastReceipt = null;
  return r;
}
