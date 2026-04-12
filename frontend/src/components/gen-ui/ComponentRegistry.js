import ThinkingSteps from './ThinkingSteps.vue'
import DataTable from './DataTable.vue'
import DataChart from './DataChart.vue'
import CitationHoverCard from './CitationHoverCard.vue'
import DocumentPreviewPanel from './DocumentPreviewPanel.vue'

export const componentRegistry = {
  ThinkingSteps,
  DataTable,
  DataChart,
  CitationHoverCard,
  DocumentPreviewPanel
}

export const getComponent = (name) => {
  return componentRegistry[name]
}

export default componentRegistry
