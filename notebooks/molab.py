import marimo

__generated_with = "0.16.3"
app = marimo.App(width="columns")

with app.setup(hide_code=True):
    import marimo as mo
    import nitro.html as rt
    from nitro.html import create_template, page_template

    hdrs = (
        rt.Link(rel="stylesheet", href="https://unpkg.com/open-props"),
        rt.Link(rel="stylesheet", href="https://unpkg.com/open-props/normalize.min.css"),
        rt.Style("""
            html {
                background: light-dark(var(--gradient-5), var(--gradient-16));
                min-height: 100vh;
                color: light-dark(var(--gray-9), var(--gray-1));
                font-family: var(--font-geometric-humanist);
                font-size: var(--font-size-1);
            }
            main {
                width: min(100% - 2rem, 45rem);
                margin-inline: auto;
            }
        """),
    )
    htmlkws = dict(lang="en")
    template = create_template(hdrs=hdrs, htmlkw=htmlkws, lucide=True)
    page = page_template(hdrs=hdrs, htmlkw=htmlkws, lucide=True)


@app.function
def show(comp: str, width="100%", height="100%"):
    return mo.iframe(str(page(comp)), width=width, height=height)


@app.cell
def _():
    myComp = rt.Div(
        # rt.H2("D* Playground"),
        rt.Button("+", on_click="$counter++"),
        rt.P("Hello from Marimo!", text="$counter"),
        rt.Button("-", on_click="$counter--"),
        style={"display: grid; gap: 1rem; width: min(100% - 2rem, 20rem); margin-inline: auto;": "$counter>0"},
        signals={"message": "Hello ", "name": "Nikola", "counter": "0"},
    )
    show(myComp)
    return


@app.cell(column=1, hide_code=True)
def _():
    mo.md(r"""## Rusty Tags performance comparison to StarHTML Tags""")
    return


@app.cell(hide_code=True)
def _():
    import time
    import functools
    from typing import Dict, List, Callable, Any
    import statistics


    class TimingResults:
        """Class to store and analyze timing results"""

        def __init__(self):
            self.results: Dict[str, List[float]] = {}

        def add_result(self, func_name: str, duration: float):
            if func_name not in self.results:
                self.results[func_name] = []
            self.results[func_name].append(duration)

        def get_stats(self, func_name: str = None):
            if func_name:
                times = self.results.get(func_name, [])
                if not times:
                    return None
                return {"function": func_name, "calls": len(times), "total": sum(times), "mean": statistics.mean(times), "median": statistics.median(times), "min": min(times), "max": max(times), "std": statistics.stdev(times) if len(times) > 1 else 0}

            # Return stats for all functions
            return {name: self.get_stats(name) for name in self.results.keys()}

        def summary(self):
            """Print a summary of all timing results"""
            print("=== Timing Results Summary ===")
            for func_name in self.results.keys():
                stats = self.get_stats(func_name)
                print(f"\n{func_name}:")
                print(f"  Calls: {stats['calls']}")
                print(f"  Mean:  {stats['mean']:.6f}s")
                print(f"  Min:   {stats['min']:.6f}s")
                print(f"  Max:   {stats['max']:.6f}s")
                if stats["std"] > 0:
                    print(f"  Std:   {stats['std']:.6f}s")


    # Global timing results storage
    timing_results = TimingResults()


    def timer(func: Callable = None, *, print_time: bool = True, store_results: bool = True, precision: int = 6) -> Callable:
        """
        Decorator to time function execution

        Args:
            print_time: Whether to print timing info after each call
            store_results: Whether to store results for later analysis
            precision: Number of decimal places for time display
        """

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.perf_counter()
                try:
                    result = f(*args, **kwargs)
                    return result
                finally:
                    end_time = time.perf_counter()
                    duration = end_time - start_time

                    if store_results:
                        timing_results.add_result(f.__name__, duration)

                    if print_time:
                        print(f"⏱️  {f.__name__}() took {duration:.{precision}f} seconds")

            return wrapper

        # Handle both @timer and @timer() usage
        if func is None:
            return decorator
        else:
            return decorator(func)


    # Convenience function to clear results
    def clear_timing_results():
        """Clear all stored timing results"""
        global timing_results
        timing_results = TimingResults()


    # Convenience function to get results
    def get_timing_results():
        """Get the global timing results object"""
        return timing_results
    return clear_timing_results, timer, timing_results


@app.cell
def _(timer):
    import starhtml as star


    @timer(print_time=False)
    def render(param: int):
        return star.Div(
            star.H1("StarHTML Demo"),
            # Define reactive state with signals
            star.Div(
                (counter := star.Signal("counter", param)),  # Python-first signal definition
                # Reactive UI that updates automatically
                star.P("Count: ", star.Span(data_text=counter)),
                star.Button("+", data_on_click=counter.add(1)),
                star.Button("Reset", data_on_click=counter.set(0)),
                # Conditional styling
                data_class_active=counter > 0,
            ),
            # Server-side interactions
            star.Button("Load Data", data_on_click=star.get("/api/data")),
            star.Div(id="content"),
        )
    return render, star


@app.cell
def _(timer):
    @timer(print_time=False)
    def rusty_render(param: int):
        signals = rt.Signals(counter=param)
        return rt.Div(
            rt.H1("StarHTML Demo"),
            # Define reactive state with signals
            rt.Div(
                # Reactive UI that updates automatically
                rt.P("Count: ", rt.Span(data_text=signals._Scounter)),
                rt.Button("+", data_on_click="$counter++"),
                rt.Button("Reset", data_on_click="$counter = 0"),
                # Conditional styling
                signals=signals,
                data_class_active="($counter > 0)",
            ),
            # Server-side interactions
            rt.Button("Load Data", data_on_click=rt.DS.get("/api/data")),
            rt.Div(id="content"),
        )
    return (rusty_render,)


@app.cell
def _(render, rusty_render):
    print(rusty_render(1))
    print(render(1))
    return


@app.cell
def _(clear_timing_results, render, rusty_render, timing_results):
    clear_timing_results()

    for i in range(10000):
        result2 = rusty_render(i)
        result = render(i)
    print(timing_results.get_stats("render")["mean"] / timing_results.get_stats("rusty_render")["mean"])
    timing_results.summary()
    return


@app.cell(column=2)
def _(star):
    class Signals(rt.AttrDict):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._signals = {}
            for key, value in kwargs.items():
                self._signals[key] = star.Signal(key, value)

        def __getattr__(self, key):
            # Return Signal object for expressions
            return self._signals.get(key)

        def to_dict(self):
            # Return plain dict for data-signals attribute
            return dict(self)
    return (Signals,)


@app.cell
def _(Signals):
    signals = Signals(counter=0)
    signals.counter.add(1)  # Signal object with methods
    print(signals.counter)
    return


@app.cell
def _(NotStr):

    s = NotStr("<script>alert('test')</script>")
    print(type(s), isinstance(s, str))  # Should be NotStr, True
    s
    return


if __name__ == "__main__":
    app.run()
