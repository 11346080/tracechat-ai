import { useEffect, useState, useRef } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import Head from 'next/head';


// 註冊 ChartJS 元素 (僅須在主檔案註冊一次就好了!!)
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// 導入類型
import { Message, DeletedMessage, HourlyTrendData, SessionId } from "../../types/chat";

// 導入元件
import Markdown from "../../components/Markdown";
import ConfirmDialog from "../../components/ConfirmDialog";
import DeletedHistoryModal from "../../components/DeletedHistoryModal";
import AnalyticsModal from "../../components/AnalyticsModal";
import Sidebar from "../../components/Sidebar";

// 導入 CSS Modules
import styles from "../styles/Home.module.css";

export default function Home() {
  const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_BASE_URL ?? "ws://localhost:8000";

  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // === 狀態管理 ===
  const [showSidebar, setShowSidebar] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [sessions, setSessions] = useState<SessionId[]>([]);
  const [currentSession, setCurrentSession] = useState<SessionId | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState<SessionId[]>([]);
  const [searchAttempted, setSearchAttempted] = useState(false);
  const [newSessionName, setNewSessionName] = useState("");
  
  const [batchMode, setBatchMode] = useState(false);
  const [checkedMap, setCheckedMap] = useState<{ [ts: number]: boolean }>({});
  
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [handleConfirm, setHandleConfirm] = useState<(() => void) | null>(null);
  
  const [deletedHistoryMessages, setDeletedHistoryMessages] = useState<DeletedMessage[]>([]);
  const [showDeletedHistoryModal, setShowDeletedHistoryModal] = useState(false);
  const [deletedBatchMode, setDeletedBatchMode] = useState(false);
  const [checkedDeletedMsgs, setCheckedDeletedMsgs] = useState<{ [key: string]: DeletedMessage }>({});
  
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [hourlyTrendData, setHourlyTrendData] = useState<HourlyTrendData[]>([]);
  
  // 新增：AI 回覆 Loading 狀態
  const [isAITyping, setIsAITyping] = useState(false);

  // === 實用函數 ===
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  // 獲取刪除歷史紀錄
async function fetchDeletedHistory(sid: string) {
  try {
    console.log(`📝 正在載入會話 ${sid} 的刪除歷史...`);
    
    const response = await fetch(
  `${API_BASE_URL}/messages/deleted_history/${encodeURIComponent(sid)}`
    );
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    const deletedMessages = data.deleted_messages || [];
    
    setDeletedHistoryMessages(deletedMessages);
    console.log(`✅ 載入了 ${deletedMessages.length} 條刪除紀錄`);
    
  } catch (error) {
    console.error("❌ 載入刪除歷史失敗:", error);
    setDeletedHistoryMessages([]);
  }
}

  // === 數據操作/API 處理函數 ===

  // 載入會話列表
  useEffect(() => {
    fetch(`${API_BASE_URL}/sessions`)
      .then(res => res.json())
      .then(data => setSessions(data.sessions));
  }, []);

  // 載入小時趨勢
  async function loadHourlyTrend() {
    if (!currentSession) return;
    try {
      const res = await fetch(
        `${API_BASE_URL}/aggregation/hourly_trend/${currentSession}`
      );

      if (!res.ok) throw new Error(`載入趨勢數據失敗, Status: ${res.status}`);
      const data = await res.json();
      if (!data.hourly_trend) throw new Error("API返回數據結構錯誤，缺少 hourly_trend 鍵");
      
      data.hourly_trend.sort((a: HourlyTrendData, b: HourlyTrendData) => {
        if (a.time_slot < b.time_slot) return -1;
        if (a.time_slot > b.time_slot) return 1;
        return 0;
      });
      
      setHourlyTrendData(data.hourly_trend);
      setShowAnalyticsModal(true);
    } catch (error) {
      console.error("載入小時趨勢失敗:", error);
      alert(`無法載入趨勢數據。錯誤訊息: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  // WebSocket 聊天 / 會話切換邏輯
  useEffect(() => {
    if (!currentSession) {
      setDeletedHistoryMessages([]);
      if (wsRef.current) wsRef.current.close();
      setIsAITyping(false);
      return;
    }

    // 立即載入刪除歷史
    fetchDeletedHistory(currentSession);

    // WebSocket 邏輯...
    if (wsRef.current) wsRef.current.close();
    setMessages([]);
    
    setCheckedMap({});
    setBatchMode(false);
    setIsAITyping(false);

    const ws = new WebSocket(
      `${WS_BASE_URL}/ws/chat/${encodeURIComponent(currentSession)}`
    );
    wsRef.current = ws;
    
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      
      if (data.sender === "AI") {
        setIsAITyping(false);
      }
      
      setMessages(msgs => {
        if (msgs.some(m => m.ts === data.ts && m.content === data.content && m.sender === data.sender)) return msgs;
        return [...msgs, data];
      });
    };
    
    return () => {
      ws.close();
      setIsAITyping(false);
    };
  }, [currentSession]);


  // 自動滾動到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages, isAITyping]);

  // 新增會話
  async function handleAddSession() {
    if (!newSessionName.trim()) return;
    const sessionName = newSessionName.trim();
    await fetch(`${API_BASE_URL}/sessions/${encodeURIComponent(sessionName)}`, {
      method: "POST",
    });
    setNewSessionName("");
    setSessions(prev => [...prev, sessionName]);
    setCurrentSession(sessionName);
  }

  // 詢問刪除會話
  function askDeleteSession(sid: string) {
    setConfirmText(`確定要刪除會話「${sid}」嗎？此動作無法復原！`);
    setConfirmOpen(true);
    setHandleConfirm(() =>
      async () => {
        await fetch(`${API_BASE_URL}/sessions/${encodeURIComponent(sid)}`, {
          method: "DELETE",
        });
        setSessions(prev => prev.filter(s => s !== sid));
        if (currentSession === sid) setCurrentSession(null);
        setConfirmOpen(false);
      });
  }

  // 發送訊息
  function handleSend() {
    if (inputMessage.trim() && wsRef.current && wsRef.current.readyState === 1) {
      wsRef.current.send(JSON.stringify({ 
        sender: "me", 
        content: inputMessage.trim(), 
        ts: Date.now() 
      }));
      setInputMessage("");
      
      // 發送後顯示 loading
      setIsAITyping(true);
      
      // 設置超時保護（30秒後自動關閉 loading）
      setTimeout(() => {
        setIsAITyping(false);
      }, 30000);
    }
  }

  // 批量刪除：詢問確認
  async function askDeleteMessagesBatch() {
    const tsList = Object.entries(checkedMap)
      .filter(([, checked]) => checked)
      .map(([ts]) => Number(ts));
      
    if (tsList.length === 0 || !currentSession) return;

    setConfirmText(`確定要批量刪除 ${tsList.length} 筆訊息嗎？此動作無法復原！`);
    setConfirmOpen(true);
    setHandleConfirm(() =>
      async () => {
        const sessionToRefresh = currentSession;
        
        try {
          console.log(`🗑️ 開始批量刪除 ${tsList.length} 條訊息...`);
          
          // 1. 呼叫後端 API 刪除
          const response = await fetch(`${API_BASE_URL}/messages/batch_delete`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: currentSession, ts_list: tsList }),
          });

          if (!response.ok) {
            throw new Error(`刪除失敗: HTTP ${response.status}`);
          }

          const result = await response.json();
          console.log(`✅ 後端回應:`, result);
          
          // 2. 更新前端狀態
          setMessages(msgs => msgs.filter(m => !tsList.includes(m.ts)));
          setCheckedMap({});
          setConfirmOpen(false);
          setBatchMode(false);

          // 3. 重新載入刪除歷史（等待後端處理完成）
          await new Promise(resolve => setTimeout(resolve, 100)); // 短暫延遲確保後端完成
          
          if (sessionToRefresh) {
            await fetchDeletedHistory(sessionToRefresh);
          }

          // 4. 重新連接 WebSocket
          if (sessionToRefresh) {
            setCurrentSession(null);
            setTimeout(() => {
              setCurrentSession(sessionToRefresh);
            }, 50);
          }

          console.log("✅ 批量刪除完成");

        } catch (err) {
          console.error("❌ 批量刪除失敗:", err);
          alert(`批量刪除失敗: ${err instanceof Error ? err.message : '未知錯誤'}`);
          setConfirmOpen(false);
        }
      });
  }



  // 訊息刪除選擇
  function toggleChecked(ts: number) {
    setCheckedMap(map => ({
      ...map,
      [ts]: !map[ts]
    }));
  }

  // 全選/清空訊息刪除選擇
  function checkAll(val: boolean) {
    let next: { [ts: number]: boolean } = {};
    messages.forEach(m => {
      next[m.ts] = val;
    });
    setCheckedMap(next);
  }

  // 全文搜尋
  function handleSearch() {
    if (!search.trim()) return;
    setSearchAttempted(true);
    fetch(
    `${API_BASE_URL}/search_messages?query=${encodeURIComponent(search)}`
    )
      .then(res => res.json())
      .then(res => setSearchResults(res.session_ids || []))
      .catch(() => setSearchResults([])); 
  }

  // 跳轉會話
  function jumpToSession(sid: string) {
    setCurrentSession(sid);
    setSearch("");
    setSearchResults([]);
    setSearchAttempted(false);
  }
  
  // 詢問復原單條刪除訊息
  function askRestoreMessage(msg: DeletedMessage) {
    setConfirmText(`確定要復原此訊息嗎？復原後將出現在聊天室中。`);
    setConfirmOpen(true);
    setHandleConfirm(() =>
      async () => {
        if (!currentSession) return;
        const sessionToRefresh = currentSession;
        
        try {
          console.log('🔄 準備復原訊息:', {
            session_id: currentSession,
            ts_to_restore: msg.ts,
            deleted_at: msg.deleted_at,
            ts_type: typeof msg.ts,
            deleted_at_type: typeof msg.deleted_at
          });
          
          const response = await fetch(`${API_BASE_URL}/messages/restore`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: currentSession,
              ts_to_restore: Number(msg.ts),
              deleted_at: Number(msg.deleted_at),
            }),
          });

          
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`復原失敗: ${JSON.stringify(errorData)}`);
          }
          
          setConfirmOpen(false);
          setShowDeletedHistoryModal(false);

          // 重新載入
          setCurrentSession(null);
          setTimeout(() => {
            setCurrentSession(sessionToRefresh);
          }, 100);
          
          console.log('✅ 訊息復原成功');
          
        } catch (err) {
          console.error("❌ 訊息復原失敗:", err);
          alert(`訊息復原失敗：${err instanceof Error ? err.message : '未知錯誤'}`);
          setConfirmOpen(false);
        }
      });
  }


  // 刪除紀錄模組：訊息選擇
  function toggleCheckedDeletedMsg(msg: DeletedMessage) {
    const key = `${msg.ts}-${msg.deleted_at}`;
    setCheckedDeletedMsgs(map => {
      const next = { ...map };
      if (next[key]) {
        delete next[key];
      } else {
        next[key] = msg;
      }
      return next;
    });
  }

  // 刪除紀錄模組：全選
  function checkAllDeletedMsgs(val: boolean) {
    const next: { [key: string]: DeletedMessage } = {};
    if (val) {
      deletedHistoryMessages.forEach(m => {
        const key = `${m.ts}-${m.deleted_at}`;
        next[key] = m;
      });
    }
    setCheckedDeletedMsgs(next);
  }

  // 批量復原：詢問確認
  function askRestoreMessagesBatch() {
    const msgsToRestore = Object.values(checkedDeletedMsgs);
    if (msgsToRestore.length === 0) return;
    
    setConfirmText(`確定要批量復原這 ${msgsToRestore.length} 筆訊息嗎？\n復原後會按照原始時間順序插入對話中。`);
    setConfirmOpen(true);
    setHandleConfirm(() =>
      async () => {
        if (!currentSession) return;
        const sessionToRefresh = currentSession;
        
        try {
          console.log(`🔄 開始批量復原 ${msgsToRestore.length} 條訊息...`);
          
          // ✅ 按時間順序復原（從舊到新）
          const sortedMsgs = [...msgsToRestore].sort((a, b) => a.ts - b.ts);
          
          for (const msg of sortedMsgs) {
            const res = await fetch(`${API_BASE_URL}/messages/restore`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                session_id: sessionToRefresh,
                ts_to_restore: Number(msg.ts),
                deleted_at: Number(msg.deleted_at),
              }),
            });

            
            if (!res.ok) {
              console.error(`⚠️ 復原失敗: ts=${msg.ts}`);
            } else {
              console.log(`✅ 已復原: ts=${msg.ts}`);
            }
          }

          setConfirmOpen(false);
          setShowDeletedHistoryModal(false);
          setDeletedBatchMode(false);
          setCheckedDeletedMsgs({});
          
          console.log(`✅ 批量復原完成，共 ${sortedMsgs.length} 條訊息`);
          
          // 重新載入會話
          setCurrentSession(null);
          setTimeout(() => {
            setCurrentSession(sessionToRefresh);
          }, 100);
          
        } catch (err) {
          console.error("❌ 訊息批量復原失敗:", err);
          alert(`訊息批量復原失敗：${err instanceof Error ? err.message : '未知錯誤'}`);
          setConfirmOpen(false);
        }
      });
  }

  // Small button style for inline use
  const smallButtonStyle: React.CSSProperties = {
    padding: "7px 12px",
    borderRadius: 5,
    backgroundColor: "#ecf0f1",
    color: "#2c3e50",
    border: "1px solid #bdc3c7",
    cursor: "pointer",
    fontSize: 12,
    fontWeight: 500,
    transition: "all 0.2s"
  };

  return (
    <>
    <Head>
      <title>全跡AI對話室</title>
      <meta name="description" content="基於 Redis + FastAPI + OpenAI 的智能對話系統" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <link rel="icon" href="/favicon.ico" />
    </Head>
    
    <div className={styles.container}>
      {/* 左側聊天室 */}
      <main className={styles.mainContent}>
        {/* 頂部標題列 */}
        <header className={styles.header}>
          {currentSession ? `會話：${currentSession}` : "🤖全跡AI對話室"}
        </header>

        {currentSession ? (
          <>
            {/* 控制工具列 */}
            <div className={styles.toolbar}>
              {/* 歷史刪除紀錄按鈕 */}
              <button
                onClick={() => setShowDeletedHistoryModal(true)}
                className={styles.deletedHistoryButton}
              >
                🗑️ 查看歷史刪除紀錄 ({deletedHistoryMessages.length})
              </button>

              {/* 批量刪除控制 */}
              <button
                onClick={() => setBatchMode(b => !b)}
                className={batchMode ? styles.batchModeActive : styles.batchModeInactive}
              >
                {batchMode ? "結束批量刪除" : "批量刪除"}
              </button>

              {batchMode && (
                <>
                  <button onClick={() => checkAll(true)} style={smallButtonStyle}>全選</button>
                  <button onClick={() => checkAll(false)} style={smallButtonStyle}>清空</button>
                  <button
                    onClick={askDeleteMessagesBatch}
                    disabled={Object.values(checkedMap).filter(v => v).length === 0}
                    style={{
                      ...smallButtonStyle,
                      background: Object.values(checkedMap).filter(v => v).length === 0 ? "#bdc3c7" : "#e74c3c",
                      color: "white",
                      cursor: Object.values(checkedMap).filter(v => v).length === 0 ? "not-allowed" : "pointer"
                    }}
                  >
                    批量刪除 (已選 {Object.values(checkedMap).filter(v => v).length} 條)
                  </button>
                </>
              )}

              {/* 活躍趨勢分析按鈕 */}
              <button
                onClick={loadHourlyTrend}
                className={styles.analyticsButton}
              >
                📈 活躍趨勢分析
              </button>
            </div>

            {/* 訊息列表區域 */}
            <div className={styles.messageListContainer}>
              {messages.length > 0 || isAITyping ? (
                <div className={styles.messageWrapper}>
                  {messages.map((m, i) => {
                    const prevMessage = i > 0 ? messages[i - 1] : null;
                    const isDifferentSender = prevMessage && prevMessage.sender !== m.sender;
                    
                    return (
                      <div
                        key={`${m.ts}-${i}`}
                        className={isDifferentSender ? styles.messageItemDifferentSender : styles.messageItem}
                      >
                        {batchMode && (
                          <input
                            type="checkbox"
                            checked={!!checkedMap[m.ts]}
                            onChange={() => toggleChecked(m.ts)}
                            className={styles.messageCheckbox}
                          />
                        )}

                        <div className={m.sender === "AI" ? styles.messageContentAI : styles.messageContentMe}>
                          <div className={m.sender === "AI" ? styles.senderLabelAI : styles.senderLabelMe}>
                            {m.sender === "AI" ? "🤖 AI 助手" : "👤 我"}
                          </div>

                          <div className={m.sender === "AI" ? styles.messageBubbleAI : styles.messageBubbleMe}>
                            <div className={styles.messageText}>
                              <Markdown content={m.content} />
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}

                  {/* Loading 動畫 */}
                  {isAITyping && (
                    <div className={styles.loadingContainer}>
                      <div className={styles.loadingContent}>
                        <div className={styles.senderLabelAI}>
                          🤖 AI 助手
                        </div>
                        <div className={styles.loadingBubble}>
                          <div className={styles.typingDot}></div>
                          <div className={styles.typingDot}></div>
                          <div className={styles.typingDot}></div>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div ref={messagesEndRef} />
                </div>
              ) : (
                <div className={styles.noMessageHint}>
                  <div className={styles.noMessageIcon}>💬</div>
                  <div className={styles.noMessageText}>還沒有對話紀錄</div>
                </div>
              )}
            </div>
            
            {/* 輸入框區域 */}
            <div className={styles.inputArea}>
              <input
                value={inputMessage}
                onChange={e => setInputMessage(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="輸入訊息..."
                className={styles.inputField}
              />
              <button
                onClick={handleSend}
                className={styles.sendButton}
              >
                發送
              </button>
            </div>
          </>
        ) : (
          <div className={styles.noSessionHint}>
            請在右側選擇一個會話來開啟新的聊天。
          </div>
        )}
      </main>

      {/* 右側 Sidebar Component */}
      <Sidebar
        showSidebar={showSidebar}
        setShowSidebar={setShowSidebar}
        sidebarWidth={sidebarWidth}
        setSidebarWidth={setSidebarWidth}
        sessions={sessions}
        currentSession={currentSession}
        setCurrentSession={setCurrentSession}
        askDeleteSession={askDeleteSession}
        newSessionName={newSessionName}
        setNewSessionName={setNewSessionName}
        handleAddSession={handleAddSession}
        search={search}
        setSearch={setSearch}
        handleSearch={handleSearch}
        searchResults={searchResults}
        jumpToSession={jumpToSession}
        searchAttempted={searchAttempted}
      />

      {/* Modal Components */}
      <DeletedHistoryModal
        showDeletedHistoryModal={showDeletedHistoryModal}
        setShowDeletedHistoryModal={setShowDeletedHistoryModal}
        deletedHistoryMessages={deletedHistoryMessages}
        currentSession={currentSession}
        askRestoreMessage={askRestoreMessage}
        askRestoreMessagesBatch={askRestoreMessagesBatch}
        setDeletedBatchMode={setDeletedBatchMode}
        deletedBatchMode={deletedBatchMode}
        checkedDeletedMsgs={checkedDeletedMsgs}
        toggleCheckedDeletedMsg={toggleCheckedDeletedMsg}
        checkAllDeletedMsgs={checkAllDeletedMsgs}
      />
      <AnalyticsModal
        showAnalyticsModal={showAnalyticsModal}
        setShowAnalyticsModal={setShowAnalyticsModal}
        hourlyTrendData={hourlyTrendData}
        currentSession={currentSession}
      />
      <ConfirmDialog
        confirmOpen={confirmOpen}
        confirmText={confirmText}
        handleConfirm={handleConfirm}
        setConfirmOpen={setConfirmOpen}
      />
    </div>
    </>
  );
}
