import { X } from "lucide-react";

export default function Modal({ title, onClose, children, maxWidth }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel" style={maxWidth ? { maxWidth } : undefined} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose} aria-label="Fermer"><X size={16} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}
