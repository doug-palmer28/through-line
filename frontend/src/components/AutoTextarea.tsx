import { useLayoutEffect, useRef, type TextareaHTMLAttributes } from "react";

/** A text box that always grows to show its whole content (no scrolling, no cut-off questions). */
export default function AutoTextarea(props: TextareaHTMLAttributes<HTMLTextAreaElement> & { value: string }) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const fit = () => {
      el.style.height = "auto";
      el.style.height = `${el.scrollHeight + 2}px`;
    };
    fit();
    const ro = new ResizeObserver(fit); // re-fit when the column gets narrower or wider
    ro.observe(el);
    window.addEventListener("resize", fit);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", fit);
    };
  }, [props.value]);

  return <textarea rows={1} {...props} ref={ref} className={`auto-textarea ${props.className ?? ""}`} />;
}
