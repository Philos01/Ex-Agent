import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'

export default function Uploads() {
  const [files, setFiles] = useState([])
  const [list, setList] = useState([])
  const [progress, setProgress] = useState({})
  const [vectorData, setVectorData] = useState({ documents: 0, memory: 0 })
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [uploading, setUploading] = useState(false)
  const fileInput = useRef(null)

  useEffect(() => {
    refreshData()
  }, [])

  const refreshData = async () => {
    setRefreshing(true)
    try {
      const documents = await loadList()
      await loadVectorData(documents)
    } finally {
      setRefreshing(false)
    }
  }

  const loadList = async () => {
    try {
      setLoading(true)
      const r = await axios.get('/api/documents')
      const documents = r.data.documents || []
      setList(documents)
      return documents
    } catch (e) {
      console.error(e)
      return []
    } finally {
      setLoading(false)
    }
  }

  const loadVectorData = async (documents) => {
    try {
      // 这里应该调用后端API获取真实的向量文档数量和内存占用
      // 由于后端没有提供这个API，我们暂时使用模拟数据
      // 实际项目中应该在后端添加相应的API端点
      const docList = documents || list
      const documentCount = docList.length * 100 // 模拟每个文档100个向量
      const memoryUsage = documentCount * 0.3 // 模拟每个向量占用0.3MB内存
      setVectorData({
        documents: documentCount,
        memory: memoryUsage
      })
    } catch (e) {
      console.error(e)
    }
  }

  const onFiles = (e) => setFiles(e.target.files)

  const upload = async () => {
    if (!files || files.length === 0) return
    setUploading(true)
    const fd = new FormData()
    for (let f of files) fd.append('files', f)
    try {
      await axios.post('/api/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (ev) => {
          setProgress({ percent: Math.round((ev.loaded / ev.total) * 100) })
        }
      })
      setFiles([])
      if (fileInput.current) fileInput.current.value = null
      setProgress({})
      await refreshData()
    } catch (e) {
      console.error('upload error', e)
      setProgress({})
    } finally {
      setUploading(false)
    }
  }

  const remove = async (name) => {
    try {
      await axios.delete('/api/documents/' + encodeURIComponent(name))
      await refreshData()
    } catch (e) {
      console.error('delete error', e)
    }
  }

  return (
    <div className="p-8 max-w-[1400px] mx-auto">
      {/* Header Section */}
      <div className="mb-10 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-on-surface mb-2">知识库</h1>
          <p className="text-on-surface-variant text-lg max-w-2xl leading-relaxed">管理和维护驱动 Luminary AI 推理引擎的通用数据和科学文档。</p>
        </div>
        <button 
          onClick={refreshData} 
          disabled={refreshing}
          className="p-3 bg-surface-container-lowest rounded-xl shadow-sm hover:bg-surface-container-low transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          <span className={`material-symbols-outlined ${refreshing ? 'animate-spin' : ''}`}>refresh</span>
          <span className="text-sm font-bold text-on-surface-variant">{refreshing ? '刷新中...' : '刷新'}</span>
        </button>
      </div>

      {/* Bento Grid Dashboard */}
      <div className="grid grid-cols-12 gap-6 mb-12">
        {/* System Integrity Metrics */}
        <div className="col-span-12 lg:col-span-4 grid grid-cols-1 gap-6">
          <div className="bg-surface-container-lowest p-6 rounded-xl shadow-[0_12px_40px_rgba(25,28,30,0.04)] flex items-center justify-between">
            <div>
              <p className="text-sm font-bold text-on-surface-variant uppercase tracking-widest mb-1">向量化文档</p>
              <h3 className="text-3xl font-black text-primary">{vectorData.documents.toLocaleString()}</h3>
              <p className="text-xs text-secondary mt-1 flex items-center gap-1"><span className="material-symbols-outlined text-xs">trending_up</span> 自上次更新</p>
            </div>
            <div className="w-16 h-16 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container">
              <span className="material-symbols-outlined text-3xl">account_tree</span>
            </div>
          </div>
          <div className="bg-surface-container-lowest p-6 rounded-xl shadow-[0_12px_40px_rgba(25,28,30,0.04)] flex items-center justify-between">
            <div>
              <p className="text-sm font-bold text-on-surface-variant uppercase tracking-widest mb-1">内存占用</p>
              <h3 className="text-3xl font-black text-tertiary">{vectorData.memory.toFixed(1)} GB</h3>
              <p className="text-xs text-on-surface-variant mt-1 opacity-70">占用率: 10GB 限制中的 {(vectorData.memory / 10 * 100).toFixed(0)}%</p>
            </div>
            <div className="w-16 h-16 rounded-full bg-tertiary-fixed flex items-center justify-center text-on-tertiary-fixed">
              <span className="material-symbols-outlined text-3xl">memory</span>
            </div>
          </div>
        </div>

        {/* Drag & Drop Zone */}
        <div className="col-span-12 lg:col-span-8 bg-surface-container-lowest p-8 rounded-xl border-2 border-dashed border-outline-variant/30 flex flex-col items-center justify-center group hover:border-primary/50 transition-colors">
          <div className="w-16 h-16 rounded-full bg-surface-container-low flex items-center justify-center text-primary group-hover:scale-110 transition-transform mb-4">
            <span className="material-symbols-outlined text-3xl">cloud_upload</span>
          </div>
          <h3 className="text-xl font-bold mb-1">当前知识库</h3>
          <p className="text-on-surface-variant text-center max-w-sm mb-6">拖放 PDF、CSV 或 XML 实验报告。Luminary AI 将自动为知识图谱向量化内容。</p>
          <div className="flex gap-4">
            <button onClick={() => fileInput.current.click()} className="px-6 py-2.5 bg-surface-container-high rounded-full font-bold text-sm hover:bg-surface-container-highest transition-colors">选择文件</button>
            <button 
              onClick={upload} 
              disabled={!files || files.length === 0 || uploading}
              className="px-6 py-2.5 bg-primary text-on-primary rounded-full font-bold text-sm shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {uploading ? (
                <>
                  <span className="material-symbols-outlined animate-spin">hourglass_empty</span>
                  处理中...
                </>
              ) : '同步知识库'}
            </button>
          </div>
          {files.length > 0 && (
            <div className="mt-4 w-full text-center">
              <p className="text-sm text-on-surface-variant">已选择 {files.length} 个文件</p>
              <ul className="mt-2 text-sm text-on-surface-variant text-left">
                {Array.from(files).map((file, index) => (
                  <li key={index}>{file.name}</li>
                ))}
              </ul>
            </div>
          )}
          <input 
            ref={fileInput} 
            type="file" 
            multiple 
            onChange={onFiles} 
            className="hidden"
          />
          {progress.percent && (
            <div className="mt-4 w-full">
              <div className="h-2 bg-surface-container-high rounded-full overflow-hidden">
                <div className="bg-primary h-2" style={{ width: progress.percent + '%' }}></div>
              </div>
              <div className="text-xs text-on-surface-variant mt-1 text-center">上传中 {progress.percent}%</div>
            </div>
          )}
        </div>
      </div>

      {/* Document Repository Table Section */}
      <div className="bg-surface-container-lowest rounded-xl shadow-[0_12px_40px_rgba(25,28,30,0.04)] overflow-hidden">
        <div className="px-8 py-6 flex items-center justify-between border-b border-surface-container-low">
          <h3 className="text-xl font-bold tracking-tight">当前知识库</h3>
          <div className="flex gap-2">
            <button className="p-2 hover:bg-surface-container-low rounded-lg transition-colors">
              <span className="material-symbols-outlined">filter_list</span>
            </button>
            <button className="p-2 hover:bg-surface-container-low rounded-lg transition-colors">
              <span className="material-symbols-outlined">more_vert</span>
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-low/50">
                <th className="px-8 py-4 text-xs font-black uppercase tracking-widest text-on-surface-variant">文件名</th>
                <th className="px-8 py-4 text-xs font-black uppercase tracking-widest text-on-surface-variant">大小</th>
                <th className="px-8 py-4 text-xs font-black uppercase tracking-widest text-on-surface-variant">上传日期</th>
                <th className="px-8 py-4 text-xs font-black uppercase tracking-widest text-on-surface-variant">状态</th>
                <th className="px-8 py-4 text-xs font-black uppercase tracking-widest text-on-surface-variant text-right">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container-low">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-8 py-10 text-center text-on-surface-variant">
                    <div className="flex items-center justify-center gap-2">
                      <span className="material-symbols-outlined animate-spin">hourglass_empty</span>
                      加载中...
                    </div>
                  </td>
                </tr>
              ) : list.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-8 py-10 text-center text-on-surface-variant">
                    暂无上传的文档
                  </td>
                </tr>
              ) : (
                list.map((d, i) => (
                  <tr key={i} className="hover:bg-surface-container-low/30 transition-colors">
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-3">
                        <div className="text-primary">
                          <span className="material-symbols-outlined">
                            {d.filename.endsWith('.pdf') ? 'description' : 
                             d.filename.endsWith('.csv') ? 'table_chart' : 
                             d.filename.endsWith('.docx') ? 'article' : 
                             d.filename.endsWith('.md') ? 'description' : 
                             d.filename.endsWith('.pptx') ? 'slideshow' : 'description'}
                          </span>
                        </div>
                        <span className="font-semibold text-sm">{d.filename}</span>
                      </div>
                    </td>
                    <td className="px-8 py-5 text-sm text-on-surface-variant">{d.size ? (d.size / 1024 / 1024).toFixed(1) + ' MB' : '未知'}</td>
                    <td className="px-8 py-5 text-sm text-on-surface-variant">{d.upload_time || '未知'}</td>
                    <td className="px-8 py-5">
                      <span className="px-3 py-1 bg-secondary-container text-on-secondary-container rounded-full text-xs font-bold flex items-center gap-1 w-max">
                        <span className="material-symbols-outlined text-[10px]" style={{ fontVariationSettings: 'FILL 1' }}>check_circle</span>
                        已向量化
                      </span>
                    </td>
                    <td className="px-8 py-5 text-right">
                      <button className="text-primary hover:bg-primary-container/10 p-2 rounded-lg transition-colors">
                        <span className="material-symbols-outlined">visibility</span>
                      </button>
                      <button 
                        onClick={() => remove(d.filename)}
                        className="text-on-surface-variant hover:bg-surface-container-low p-2 rounded-lg transition-colors ml-1"
                      >
                        <span className="material-symbols-outlined">delete_outline</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {/* Pagination */}
        <div className="px-8 py-4 bg-surface-container-low/30 flex justify-between items-center">
          <p className="text-xs font-semibold text-on-surface-variant opacity-60">显示 1,284 份文档中的 4 份</p>
          <div className="flex gap-2">
            <button className="p-1 rounded hover:bg-surface-container-low transition-colors disabled:opacity-30" disabled>
              <span className="material-symbols-outlined">chevron_left</span>
            </button>
            <button className="p-1 rounded hover:bg-surface-container-low transition-colors">
              <span className="material-symbols-outlined">chevron_right</span>
            </button>
          </div>
        </div>
      </div>

      {/* Contextual FAB - Only for main dashboards */}
      <button className="fixed bottom-8 right-8 w-14 h-14 bg-gradient-to-tr from-primary to-primary-container text-on-primary rounded-full shadow-2xl flex items-center justify-center group active:scale-90 transition-transform">
        <span className="material-symbols-outlined text-3xl">add</span>
        <span className="absolute right-full mr-4 bg-inverse-surface text-inverse-on-surface px-3 py-1.5 rounded-lg text-sm font-bold opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-lg">新建会话</span>
      </button>
    </div>
  )
}
