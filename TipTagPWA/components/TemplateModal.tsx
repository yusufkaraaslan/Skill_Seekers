'use client'

import { Template, templates } from '@/utils/templates'

interface TemplateModalProps {
  isOpen: boolean
  onClose: () => void
  onSelect: (template: Template) => void
}

export default function TemplateModal({ isOpen, onClose, onSelect }: TemplateModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">選擇模板</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
          >
            <span className="text-gray-500 text-xl">✕</span>
          </button>
        </div>

        {/* Template Grid */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-gray-900">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.map((template) => (
              <div
                key={template.id}
                onClick={() => onSelect(template)}
                className="group bg-white dark:bg-gray-800 p-5 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-500 hover:shadow-md cursor-pointer transition-all"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="text-3xl">{template.icon}</div>
                  <span className="text-gray-300 group-hover:text-primary-500 transform group-hover:translate-x-1 transition-all">
                    →
                  </span>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  {template.name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                  {template.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-right">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 font-medium"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  )
}
