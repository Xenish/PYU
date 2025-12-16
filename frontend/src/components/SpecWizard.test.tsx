import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SpecWizard } from "./SpecWizard";

type DetailState = ReturnType<typeof createDetailState>;

let detailState: DetailState;
let summaryState: any;

const getWizardDetailMock = vi.fn();
const getWizardSummaryMock = vi.fn();
const toggleItemSelectionMock = vi.fn();
const selectAllItemsMock = vi.fn();
const deselectAllItemsMock = vi.fn();
const getSelectionSummaryMock = vi.fn();
const approveStepMock = vi.fn();
const rejectStepMock = vi.fn();
const regenerateStepMock = vi.fn();
const runObjectiveMock = vi.fn();
const runTechStackMock = vi.fn();
const runFeaturesMock = vi.fn();
const runArchitectureMock = vi.fn();
const runQualityMock = vi.fn();

vi.mock("@/lib/api", () => ({
  StepStatus: {},
  getWizardDetail: (...args: any[]) => getWizardDetailMock(...args),
  getWizardSummary: (...args: any[]) => getWizardSummaryMock(...args),
  toggleItemSelection: (...args: any[]) => toggleItemSelectionMock(...args),
  selectAllItems: (...args: any[]) => selectAllItemsMock(...args),
  deselectAllItems: (...args: any[]) => deselectAllItemsMock(...args),
  getSelectionSummary: (...args: any[]) => getSelectionSummaryMock(...args),
  approveStep: (...args: any[]) => approveStepMock(...args),
  rejectStep: (...args: any[]) => rejectStepMock(...args),
  regenerateStep: (...args: any[]) => regenerateStepMock(...args),
  runObjective: (...args: any[]) => runObjectiveMock(...args),
  runTechStack: (...args: any[]) => runTechStackMock(...args),
  runFeatures: (...args: any[]) => runFeaturesMock(...args),
  runArchitecture: (...args: any[]) => runArchitectureMock(...args),
  runQuality: (...args: any[]) => runQualityMock(...args),
}));

function createDetailState() {
  return {
    objectives: [{ id: 1, title: "O1", text: "desc", is_selected: false }],
    tech_stack: [
      {
        id: 2,
        frontend: { name: "Next.js" },
        backend: { name: "FastAPI" },
        is_selected: false,
      },
    ],
    features: [
      { id: 3, name: "F1", description: "d1", is_selected: false },
      { id: 4, name: "F2", description: "d2", is_selected: false },
    ],
    architecture: [{ id: 5, name: "C1", layer: "backend", description: "d", is_selected: false }],
    dod_items: [{ id: 6, description: "DoD", category: "cat", is_selected: false }],
    nfr_items: [{ id: 7, type: "perf", description: "fast", is_selected: false }],
    risk_items: [{ id: 8, description: "Risk", is_selected: false }],
  };
}

function createSummaryState(detail: DetailState) {
  return {
    project_id: 1,
    steps: [
      { step_type: "objective", status: "completed", approval_status: "pending", item_count: detail.objectives.length, summary: "O1" },
      { step_type: "tech_stack", status: "completed", approval_status: "pending", item_count: detail.tech_stack.length, summary: "Tech" },
      { step_type: "features", status: "completed", approval_status: "pending", item_count: detail.features.length, summary: "Feat" },
      { step_type: "architecture", status: "completed", approval_status: "pending", item_count: detail.architecture.length, summary: "Arch" },
      { step_type: "dod", status: "completed", approval_status: "pending", item_count: detail.dod_items.length + detail.nfr_items.length + detail.risk_items.length, summary: "Quality" },
    ],
  };
}

function getItemsByType(itemType: string) {
  switch (itemType) {
    case "objective":
      return detailState.objectives;
    case "tech_stack":
      return detailState.tech_stack;
    case "feature":
      return detailState.features;
    case "architecture":
      return detailState.architecture;
    case "dod":
      return detailState.dod_items;
    case "nfr":
      return detailState.nfr_items;
    case "risk":
      return detailState.risk_items;
    default:
      return [];
  }
}

beforeEach(() => {
  detailState = createDetailState();
  summaryState = createSummaryState(detailState);

  getWizardDetailMock.mockImplementation(async () => JSON.parse(JSON.stringify(detailState)));
  getWizardSummaryMock.mockImplementation(async () => summaryState);
  toggleItemSelectionMock.mockImplementation(async (_projectId: number, itemType: string, itemId: number) => {
    const items = getItemsByType(itemType);
    const target = items.find((i) => i.id === itemId);
    if (target) {
      target.is_selected = !target.is_selected;
    }
  });
  selectAllItemsMock.mockImplementation(async (_projectId: number, itemType: string) => {
    const items = getItemsByType(itemType);
    items.forEach((i) => (i.is_selected = true));
  });
  deselectAllItemsMock.mockImplementation(async (_projectId: number, itemType: string) => {
    const items = getItemsByType(itemType);
    items.forEach((i) => (i.is_selected = false));
  });
  getSelectionSummaryMock.mockImplementation(async (_projectId: number, itemType: string) => {
    const items = getItemsByType(itemType);
    return {
      project_id: 1,
      item_type: itemType,
      selected_count: items.filter((i) => i.is_selected).length,
      total_count: items.length,
    };
  });
  approveStepMock.mockImplementation(async (_projectId: number, stepType: string) => {
    const step = summaryState.steps.find((s: any) => s.step_type === stepType);
    if (step) {
      step.approval_status = "approved";
    }
  });
  rejectStepMock.mockResolvedValue({});
  regenerateStepMock.mockResolvedValue({});
  runObjectiveMock.mockResolvedValue({});
  runTechStackMock.mockResolvedValue({});
  runFeaturesMock.mockResolvedValue({});
  runArchitectureMock.mockResolvedValue({});
  runQualityMock.mockResolvedValue({});
});

describe("SpecWizard item selection UI", () => {
  it("renders checkboxes for each item", async () => {
    render(<SpecWizard projectId={1} />);
    const checkboxes = await screen.findAllByRole("checkbox");
    expect(checkboxes.length).toBe(8);
  });

  it("toggles checkbox selection on click", async () => {
    render(<SpecWizard projectId={1} />);
    const user = userEvent.setup();
    const firstCheckbox = await screen.findAllByRole("checkbox").then((cbs) => cbs[0]);
    expect(firstCheckbox).not.toBeChecked();
    await user.click(firstCheckbox);
    await waitFor(() => expect(firstCheckbox).toBeChecked());
  });

  it("select all and deselect all buttons update items", async () => {
    render(<SpecWizard projectId={1} />);
    const user = userEvent.setup();
    const featuresHeader = await screen.findByText("Özellikler");
    const featureSection = featuresHeader.parentElement?.parentElement as HTMLElement;
    const selectAllBtn = within(featureSection).getAllByText("Tümünü Seç")[0];
    const deselectAllBtn = within(featureSection).getAllByText("Seçimi Kaldır")[0];

    await user.click(selectAllBtn);
    await waitFor(() => {
      const featureCheckboxes = within(featureSection).getAllByRole("checkbox");
      expect(featureCheckboxes.every((cb) => cb instanceof HTMLInputElement && cb.checked)).toBe(true);
    });

    await user.click(deselectAllBtn);
    await waitFor(() => {
      const featureCheckboxes = within(featureSection).getAllByRole("checkbox");
      expect(featureCheckboxes.every((cb) => cb instanceof HTMLInputElement && !cb.checked)).toBe(true);
    });
  });

  it("disables approve button when no items selected", async () => {
    render(<SpecWizard projectId={1} />);
    const archHeader = await screen.findByText("Mimari");
    const card = archHeader.closest(".rounded") as HTMLElement;
    const approveBtn = within(card).getByRole("button", { name: /Seçilenleri Onayla/ });
    expect(approveBtn).toBeDisabled();
  });

  it("disables checkboxes when step is approved", async () => {
    summaryState.steps.find((s: any) => s.step_type === "features")!.approval_status = "approved";
    render(<SpecWizard projectId={1} />);
    const featuresHeader = await screen.findByText("Özellikler");
    const featureSection = featuresHeader.parentElement?.parentElement as HTMLElement;
    const featureCheckboxes = within(featureSection).getAllByRole("checkbox");
    featureCheckboxes.forEach((cb) => expect(cb).toBeDisabled());
  });

  it("shows selection summary counts", async () => {
    detailState.features[0].is_selected = true;
    render(<SpecWizard projectId={1} />);
    await screen.findByText(/Seçilenleri Onayla/); // ensure section rendered
    const summaryText = await screen.findByText(/1 \/ 2 öğe seçili/);
    expect(summaryText).toBeInTheDocument();
  });
});
