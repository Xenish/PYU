import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { PlanningView } from "@/components/PlanningView";
import * as api from "@/lib/api";

describe("PlanningView", () => {
  it("renders epics and sprints", async () => {
    vi.spyOn(api, "getPlanningOverview").mockResolvedValue({
      project_id: 1,
      epics: [
        { id: 1, name: "Epic A", category: "feature", story_points: 5, sprint_ids: [1], dependencies: [] },
      ],
      sprints: [
        {
          id: 1,
          name: "Sprint 1",
          capacity_sp: 10,
          allocated_sp: 5,
          epic_ids: [1],
          quality_summary: { dod_count: 2, nfr_categories: ["perf"] },
        },
      ],
    } as any);

    render(<PlanningView projectId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Epic A")).toBeInTheDocument();
    });
    expect(screen.getByText("Sprint 1")).toBeInTheDocument();
  });
});
