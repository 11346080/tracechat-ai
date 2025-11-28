interface ConfirmDialogProps {
  confirmOpen: boolean;
  confirmText: string;
  handleConfirm: (() => void) | null;
  setConfirmOpen: (open: boolean) => void;
}

export default function ConfirmDialog({
  confirmOpen,
  confirmText,
  handleConfirm,
  setConfirmOpen
}: ConfirmDialogProps) {
  if (!confirmOpen) return null;
  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(0,0,0,0.6)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 2000,
      padding: "20px"
    }}>
      <div style={{
        background: "white",
        padding: "24px",
        borderRadius: 12,
        maxWidth: 400,
        width: "100%",
        boxShadow: "0 4px 16px rgba(0,0,0,0.3)"
      }}>
        <div style={{ marginBottom: 20, fontSize: 15, color: "#2c3e50", lineHeight: 1.6 }}>
          {confirmText}
        </div>
        <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
          <button
            onClick={() => handleConfirm?.()}
            style={{
              background: "#e74c3c",
              color: "white",
              border: "none",
              padding: "10px 20px",
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 14,
              fontWeight: 600
            }}
          >
            確定
          </button>
          <button
            onClick={() => setConfirmOpen(false)}
            style={{
              background: "#ecf0f1",
              color: "#2c3e50",
              border: "none",
              padding: "10px 20px",
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 14,
              fontWeight: 600
            }}
          >
            取消
          </button>
        </div>
      </div>
    </div>
  );
}