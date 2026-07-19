import { useState, useCallback, useEffect } from 'react'

/**
 * Hook that tracks text selection within a given container ref.
 * Returns selectedText, selectionRect (for positioning toolbar), and clearSelection.
 *
 * Usage:
 *   const containerRef = useRef(null)
 *   const { selectedText, selectionRect, clearSelection } = useTextSelection(containerRef)
 *   {selectedText && <TextSelectionToolbar rect={selectionRect} text={selectedText} ... />}
 */
export default function useTextSelection(containerRef) {
  const [selectedText, setSelectedText] = useState('')
  const [selectionRect, setSelectionRect] = useState(null)

  const clearSelection = useCallback(() => {
    setSelectedText('')
    setSelectionRect(null)
    window.getSelection()?.removeAllRanges()
  }, [])

  useEffect(() => {
    const el = containerRef?.current
    if (!el) return

    function handleMouseUp(e) {
      // Small delay so browser finishes updating selection
      requestAnimationFrame(() => {
        const sel = window.getSelection()
        if (!sel || sel.isCollapsed || !sel.toString().trim()) {
          setSelectedText('')
          setSelectionRect(null)
          return
        }

        const text = sel.toString().trim()
        if (text.length < 2) {
          setSelectedText('')
          setSelectionRect(null)
          return
        }

        // Check if selection is inside our container
        const range = sel.getRangeAt(0)
        if (!el.contains(range.commonAncestorContainer)) {
          setSelectedText('')
          setSelectionRect(null)
          return
        }

        const rect = range.getBoundingClientRect()
        setSelectedText(text)
        setSelectionRect({
          top: rect.top,
          bottom: rect.bottom,
          left: rect.left + rect.width / 2, // center of selection
          width: rect.width,
        })
      })
    }

    el.addEventListener('mouseup', handleMouseUp)
    return () => el.removeEventListener('mouseup', handleMouseUp)
  }, [containerRef])

  // dismiss on click outside
  useEffect(() => {
    if (!selectedText) return
    function handleClick(e) {
      if (containerRef?.current && !containerRef.current.contains(e.target)) {
        clearSelection()
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [selectedText, clearSelection, containerRef])

  return { selectedText, selectionRect, clearSelection }
}
