import { DeletedMessage } from '../types/chat';
import { smallButtonStyle } from '../utils/styles';
import Markdown from './Markdown';

interface DeletedHistoryModalProps {
  showDeletedHistoryModal: boolean;
  setShowDeletedHistoryModal: (show: boolean) => void;
  deletedHistoryMessages: DeletedMessage[];
  currentSession: string | null;
  askRestoreMessage: (msg: DeletedMessage) => void;
  askRestoreMessagesBatch: () => void;
  setDeletedBatchMode: (mode: boolean | ((prevState: boolean) => boolean)) => void; 
  deletedBatchMode: boolean;
  checkedDeletedMsgs: { [key: string]: DeletedMessage };
  toggleCheckedDeletedMsg: (msg: DeletedMessage) => void;
  checkAllDeletedMsgs: (val: boolean) => void;
}

export default function DeletedHistoryModal({
  showDeletedHistoryModal,
  setShowDeletedHistoryModal,
  deletedHistoryMessages,
  currentSession,
  askRestoreMessage,
  askRestoreMessagesBatch,
  setDeletedBatchMode,
  deletedBatchMode,
  checkedDeletedMsgs,
  toggleCheckedDeletedMsg,
  checkAllDeletedMsgs,
}: DeletedHistoryModalProps) {
  if (!showDeletedHistoryModal) return null;
  const selectedCount = Object.keys(checkedDeletedMsgs).length;
  const totalCount = deletedHistoryMessages.length;
  const isAllChecked = totalCount > 0 && selectedCount === totalCount;

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(0,0,0,0.5)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 1000,
      padding: "20px"
    }}>
      <div style={{
        background: "white",
        padding: "24px",
        borderRadius: 12,
        maxWidth: 700,
        width: "100%",
        maxHeight: "80vh",
        overflowY: "auto",
        boxShadow: "0 4px 16px rgba(0,0,0,0.2)"
      }}>
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
          paddingBottom: 12,
          borderBottom: "2px solid #e1e8ed"
        }}>
          <h2 style={{ margin: 0, fontSize: 20, color: "#2c3e50" }}>
            {currentSession}-歷史刪除紀錄 (僅保存30天)
          </h2>
          <button
            onClick={() => setShowDeletedHistoryModal(false)}
            style={{
              background: "#e74c3c",
              color: "white",
              border: "none",
              padding: "8px 16px",
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 14,
              fontWeight: 500
            }}
          >
            關閉 ✕
          </button>
        </div>

        {deletedHistoryMessages.length > 0 && (
          <div style={{ marginBottom: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button
              onClick={() => setDeletedBatchMode(b => !b)}
              style={{
                background: deletedBatchMode ? "#e74c3c" : "#ecf0f1",
                color: deletedBatchMode ? "white" : "#2c3e50",
                border: "none",
                padding: "8px 14px",
                borderRadius: 6,
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 500
              }}
            >
              {deletedBatchMode ? "結束批量模式" : "批量復原"}
            </button>
            {deletedBatchMode && (
              <>
                <button
                  onClick={() => checkAllDeletedMsgs(!isAllChecked)}
                  disabled={totalCount === 0}
                  style={{
                    ...smallButtonStyle,
                    cursor: totalCount === 0 ? "not-allowed" : "pointer",
                    opacity: totalCount === 0 ? 0.5 : 1
                  }}
                >
                  {isAllChecked ? "取消全選" : "全選"}
                </button>
                <button
                  onClick={askRestoreMessagesBatch}
                  disabled={selectedCount === 0}
                  style={{
                    ...smallButtonStyle,
                    background: selectedCount === 0 ? "#bdc3c7" : "#27ae60",
                    color: "white",
                    cursor: selectedCount === 0 ? "not-allowed" : "pointer"
                  }}
                >
                  ↩️ 批量復原 ({selectedCount})
                </button>
              </>
            )}
          </div>
        )}

        {deletedHistoryMessages.length === 0 ? (
          <div style={{ padding: "40px 20px", textAlign: "center", color: "#95a5a6", fontSize: 15 }}>
            此會話沒有刪除紀錄。
          </div>
        ) : (
          <div>
            {deletedHistoryMessages.map((m, index) => {
              const key = `${m.ts}-${m.deleted_at}`;
              return (
                <div
                  key={key}
                  style={{
                    padding: "12px 16px",
                    marginBottom: 12,
                    background: "#f8f9fa",
                    borderRadius: 8,
                    border: "1px solid #e1e8ed",
                    display: "flex",
                    gap: 12
                  }}
                >
                  {deletedBatchMode && (
                    <input
                      type="checkbox"
                      checked={!!checkedDeletedMsgs[key]}
                      onChange={() => toggleCheckedDeletedMsg(m)}
                      style={{ marginTop: 5, cursor: "pointer", width: 16, height: 16 }}
                    />
                  )}
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, color: "#7f8c8d", marginBottom: 8 }}>
                      原始時間: {new Date(m.ts).toLocaleString()} | 刪除時間: {new Date(m.deleted_at * 1000).toLocaleString()}
                    </div>
                    <div style={{ fontSize: 14, color: "#2c3e50", lineHeight: 1.5 }}>
                      <Markdown content={m.content} />
                    </div>
                    {!deletedBatchMode && (
                      <button
                        onClick={() => askRestoreMessage(m)}
                        style={{
                          marginTop: 8,
                          background: "#27ae60",
                          color: "white",
                          border: "none",
                          padding: "6px 12px",
                          borderRadius: 6,
                          cursor: "pointer",
                          fontSize: 13,
                          fontWeight: 500
                        }}
                      >
                        ↩️ 復原
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}