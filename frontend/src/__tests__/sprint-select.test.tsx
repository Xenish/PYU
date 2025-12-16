import { render, screen } from "@testing-library/react";
import { SprintSelect } from "@/components/SprintSelect";

describe("SprintSelect", () => {
  it("shows placeholder when disabled", () => {
    render(
      <SprintSelect
        sprints={[]}
        selectedSprint={null}
        onSelect={() => {}}
        disabled
      />
    );
    expect(screen.getByText("Önce proje seçin")).toBeInTheDocument();
  });
});
