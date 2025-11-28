import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { HourlyTrendData } from '../types/chat';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface AnalyticsModalProps {
  showAnalyticsModal: boolean;
  setShowAnalyticsModal: (show: boolean) => void;
  hourlyTrendData: HourlyTrendData[];
  currentSession: string | null;
}

export default function AnalyticsModal({
  showAnalyticsModal,
  setShowAnalyticsModal,
  hourlyTrendData,
  currentSession
}: AnalyticsModalProps) {
    if (!showAnalyticsModal || !currentSession) return null;

    // 格式化時間的函數
    const formatTimeSlot = (time_slot: string) => {
        const standardDateString = time_slot.replace(/-/g, "/");
        const date = new Date(standardDateString);
        if (isNaN(date.getTime())) {
          return "無效時間";
        }
        const timePart = date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
        const datePart = `${date.getMonth() + 1}/${date.getDate()}`;
        return `${timePart} (${datePart})`;
    };

    const chartData = {
      labels: hourlyTrendData.map(d => formatTimeSlot(d.time_slot)),
      datasets: [
        {
          label: '訊息數量',
          data: hourlyTrendData.map(d => d.count),
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1,
        },
      ],
    };

    const chartOptions = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: `${currentSession} - 聊天會話小時活躍趨勢 (RediSearch 聚合結果)`,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: '訊息數量 (Count)',
          },
          ticks: {
            callback: (value: any) => { if (value % 1 === 0) return value; },
          },
        },
        x: {
          type: 'category' as const,
          labels: hourlyTrendData.map(d => formatTimeSlot(d.time_slot)),
          title: {
            display: true,
            text: '時間段 (小時)',
          },
        },
      },
    };

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
          maxWidth: 900,
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
              📈 活躍趨勢分析 - {currentSession}
            </h2>
            <button
              onClick={() => setShowAnalyticsModal(false)}
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

          {hourlyTrendData.length > 0 ? (
            <Bar data={chartData} options={chartOptions} />
          ) : (
            <div style={{ padding: "40px 20px", textAlign: "center", color: "#95a5a6", fontSize: 15 }}>
              此會話數據不足，無法繪製趨勢圖。
            </div>
          )}
        </div>
      </div>
    );
}