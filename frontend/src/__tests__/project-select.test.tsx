import { render, screen, fireEvent } from "@testing-library/react";
import { ProjectSelect } from "@/components/ProjectSelect";

describe("ProjectSelect", () => {
  it("renders projects and handles selection", () => {
    const projects = [
      { id: 1, name: "P1" },
      { id: 2, name: "P2" },
    ];
    const onSelect = vi.fn();
    render(
      <ProjectSelect
        projects={projects}
        selectedProject={null}
        onSelect={onSelect}
      />
    );
    expect(screen.getByText("P1")).toBeInTheDocument();
    fireEvent.click(screen.getByText("P2"));
    expect(onSelect).toHaveBeenCalledWith(2);
  });
});
