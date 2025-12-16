import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { SprintTaskBoard } from "@/components/SprintTaskBoard";
import * as api from "@/lib/api";

describe("SprintTaskBoard", () => {
  it("groups tasks by status and updates", async () => {
    vi.spyOn(api, "getTasksForBoard").mockResolvedValue([
      { id: 1, title: "Task 1", status: "todo", epic_name: "Epic X" },
    ] as any);
    const updateSpy = vi.spyOn(api, "updateTaskStatus").mockResolvedValue({
      id: 1,
      title: "Task 1",
      status: "in_progress",
      epic_name: "Epic X",
    } as any);

    render(<SprintTaskBoard sprintId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Task 1")).toBeInTheDocument();
    });

    const select = screen.getByDisplayValue("Planlandı");
    fireEvent.change(select, { target: { value: "in_progress" } });

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalled();
    });
  });
});
