import { useState, useRef, useEffect } from 'react'
import { Info } from 'lucide-react'

export default function Tooltip({ content, children }) {
  const [visible, setVisible] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    if (!mobileOpen) return
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setMobileOpen(false)
    }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [mobileOpen])

  return (
    <div
      ref={ref}
      className="relative inline-flex items-center gap-1"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      <button
        type="button"
        className="md:hidden text-zinc-500 hover:text-cyan-400 transition-colors p-0.5"
        onClick={(e) => {
          e.stopPropagation()
          setMobileOpen((v) => !v)
        }}
        aria-label="상세 정보"
      >
        <Info size={14} />
      </button>
      {(visible || mobileOpen) && (
        <div
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 max-w-[calc(100vw-2rem)] px-3 py-2 text-xs leading-relaxed text-zinc-200 bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl pointer-events-none md:pointer-events-auto"
          role="tooltip"
        >
          {content}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-zinc-800" />
        </div>
      )}
    </div>
  )
}
