import React, { useRef, useEffect } from 'react';
import { SessionId } from '../types/chat';

interface SidebarProps {
  showSidebar: boolean;
  setShowSidebar: (show: boolean) => void;
  sidebarWidth: number;
  setSidebarWidth: (width: number) => void;
  sessions: SessionId[];
  currentSession: SessionId | null;
  setCurrentSession: (sid: SessionId | null) => void;
  askDeleteSession: (sid: SessionId) => void;
  newSessionName: string;
  setNewSessionName: (name: string) => void;
  handleAddSession: () => Promise<void>;
  search: string;
  setSearch: (query: string) => void;
  handleSearch: () => void;
  searchResults: SessionId[];
  jumpToSession: (sid: SessionId) => void;
  searchAttempted: boolean;
}

export default function Sidebar({
  showSidebar,
  setShowSidebar,
  sidebarWidth,
  setSidebarWidth,
  sessions,
  currentSession,
  setCurrentSession,
  askDeleteSession,
  newSessionName,
  setNewSessionName,
  handleAddSession,
  search,
  setSearch,
  handleSearch,
  searchResults,
  jumpToSession,
  searchAttempted
}: SidebarProps) {
  const sidebarRef = useRef<HTMLElement>(null);
  const isDragging = useRef(false);
  
  // 拖曳邏輯
  function startDrag(e: React.MouseEvent) {
    isDragging.current = true;
    document.body.style.cursor = "col-resize";
  }

  function endDrag() {
    isDragging.current = false;
    document.body.style.cursor = "";
  }

  function handleDrag(e: MouseEvent) {
    if (isDragging.current) {
      // 從右側計算寬度
      const rightEdge = window.innerWidth - e.clientX;
      setSidebarWidth(Math.max(180, Math.min(480, rightEdge)));
    }
  }

  useEffect(() => {
    function onMouseMove(e: MouseEvent) { handleDrag(e) }
    function onMouseUp() { endDrag() }
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    // 移除依賴項中關於 setSidebarWidth 的警告，因為它是外部傳入的 state setter
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [setSidebarWidth]); 

  // 當 Sidebar 隱藏時，只渲染展開按鈕
  if (!showSidebar) {
    return (
      <button
        onClick={() => setShowSidebar(true)}
        style={{
          position: "fixed",
          right: 16,
          top: 8,
          background: "#2c3e50",
          color: "white",
          border: "none",
          padding: "12px 16px",
          borderRadius: 8,
          cursor: "pointer",
          fontSize: 16,
          boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
          zIndex: 100,
          transition: "background 0.2s"
        }}
        onMouseEnter={e => e.currentTarget.style.background = "#34495e"}
        onMouseLeave={e => e.currentTarget.style.background = "#2c3e50"}
      >
        ☰ 展開
      </button>
    );
  }

  return (
    <aside
      ref={sidebarRef}
      style={{
        width: sidebarWidth,
        minWidth: 180,
        maxWidth: 480,
        height: "100%",
        backgroundColor: "#2c3e50",
        color: "white",
        padding: "20px 16px",
        overflowY: "auto",
        boxShadow: "-2px 0 8px rgba(0,0,0,0.1)",
        position: "relative",
        transition: "width 0.1s ease-out"
      }}
    >
      {/* 隱藏按鈕 */}
      <button
        onClick={() => setShowSidebar(false)}
        style={{
          position: "absolute",
          top: 12,
          right: 12,
          background: "rgba(255,255,255,0.15)",
          color: "white",
          border: "none",
          padding: "6px 10px",
          borderRadius: 6,
          cursor: "pointer",
          fontSize: 12,
          transition: "background 0.2s"
        }}
        onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.25)"}
        onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.15)"}
      >
        隱藏會話列表
      </button>

      <h2 style={{ marginTop: 0, marginBottom: 20, fontSize: 18, fontWeight: 600 }}>會話列表</h2>

      {/* 會話列表 */}
      <div style={{ marginBottom: 24 }}>
        {(sessions || []).map(sid => (
          <div
            key={sid}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "10px 12px",
              marginBottom: 8,
              backgroundColor: currentSession === sid ? "#34495e" : "rgba(255,255,255,0.08)",
              borderRadius: 8,
              cursor: "pointer",
              transition: "background 0.2s",
              fontSize: 14
            }}
            onClick={() => setCurrentSession(sid)}
            onMouseEnter={e => e.currentTarget.style.backgroundColor = currentSession === sid ? "#34495e" : "rgba(255,255,255,0.15)"}
            onMouseLeave={e => e.currentTarget.style.backgroundColor = currentSession === sid ? "#34495e" : "rgba(255,255,255,0.08)"}
          >
            <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{sid}</span>
            <button
              onClick={(e) => { e.stopPropagation(); askDeleteSession(sid); }}
              style={{
                background: "rgba(231, 76, 60, 0.8)",
                border: "none",
                color: "white",
                padding: "4px 8px",
                borderRadius: 4,
                cursor: "pointer",
                fontSize: 14,
                transition: "background 0.2s"
              }}
              onMouseEnter={e => e.currentTarget.style.background = "rgba(231, 76, 60, 1)"}
              onMouseLeave={e => e.currentTarget.style.background = "rgba(231, 76, 60, 0.8)"}
            >
              🗑️
            </button>
          </div>
        ))}
      </div>

      {/* 新增會話 */}
      <div style={{ marginBottom: 24 }}>
        <input
          value={newSessionName}
          onChange={e => setNewSessionName(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleAddSession()}
          placeholder="新會話ID"
          style={{
            width: "100%",
            padding: "10px 12px",
            marginBottom: 8,
            border: "none",
            borderRadius: 6,
            fontSize: 14,
            boxSizing: "border-box"
          }}
        />
        <button
          onClick={handleAddSession}
          style={{
            width: "100%",
            padding: "10px 12px",
            background: "#27ae60",
            color: "white",
            border: "none",
            borderRadius: 6,
            cursor: "pointer",
            fontSize: 14,
            fontWeight: 500,
            transition: "background 0.2s"
          }}
          onMouseEnter={e => e.currentTarget.style.background = "#229954"}
          onMouseLeave={e => e.currentTarget.style.background = "#27ae60"}
        >
          新增
        </button>
      </div>

      {/* 全文搜尋 */}
      <div>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, opacity: 0.9 }}>全文搜尋會話</h3>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="輸入關鍵字"
          onKeyDown={e => e.key === "Enter" && handleSearch()}
          style={{
            width: "100%",
            padding: "10px 12px",
            marginBottom: 8,
            border: "none",
            borderRadius: 6,
            fontSize: 14,
            boxSizing: "border-box"
          }}
        />
        <button
          onClick={handleSearch}
          style={{
            width: "100%",
            padding: "10px 12px",
            background: "#3498db",
            color: "white",
            border: "none",
            borderRadius: 6,
            cursor: "pointer",
            fontSize: 14,
            fontWeight: 500,
            marginBottom: 8,
            transition: "background 0.2s"
          }}
          onMouseEnter={e => e.currentTarget.style.background = "#2980b9"}
          onMouseLeave={e => e.currentTarget.style.background = "#3498db"}
        >
          搜尋
        </button>
        
        {/* 搜尋結果顯示或查無資料提示 */}
        {searchResults.length > 0 ? (
          (searchResults || []).map(sid => (
            <div
              key={sid}
              onClick={() => jumpToSession(sid)}
              style={{
                padding: "8px 12px",
                background: "rgba(46, 204, 113, 0.2)",
                borderRadius: 6,
                cursor: "pointer",
                marginBottom: 6,
                fontSize: 13,
                border: "1px solid rgba(46, 204, 113, 0.4)",
                transition: "background 0.2s"
              }}
              onMouseEnter={e => e.currentTarget.style.background = "rgba(46, 204, 113, 0.3)"}
              onMouseLeave={e => e.currentTarget.style.background = "rgba(46, 204, 113, 0.2)"}
            >
              跳到會話：{sid}
            </div>
          ))
        ) : searchAttempted && search.trim() ? (
          <div style={{ padding: "8px 12px", color: "#e74c3c", fontSize: 13 }}>
            查無此資料
          </div>
        ) : null}
      </div>

      {/* 拖曳控制條 */}
      <div
        onMouseDown={startDrag}
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: 4,
          cursor: "col-resize",
          background: "rgba(255,255,255,0.1)",
          transition: "background 0.2s"
        }}
        onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.3)"}
        onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.1)"}
      />
    </aside>
  );
}