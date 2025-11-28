import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import dynamic from "next/dynamic";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";

// 動態導入 SyntaxHighlighter 以支援 SSR
const SyntaxHighlighter = dynamic(
  () => import("react-syntax-highlighter").then(mod => mod.Prism),
  { ssr: false }
);

interface MarkdownProps {
  content: string;
}

export default function Markdown({ content }: MarkdownProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ node, inline, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || "");
          return !inline && match ? (
            <SyntaxHighlighter
              style={oneLight}
              language={match[1]}
              PreTag="div"
              {...props}
            >
              {String(children).replace(/\n$/, "")}
            </SyntaxHighlighter>
          ) : (
            <code className={className} {...props}>
              {children}
            </code>
          );
        }
      }}
    >
      {content}
    </ReactMarkdown>
  );
}