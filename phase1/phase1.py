import io_mod
import sim_mod

# Creating a backend that references all central functions,
# making them easily accessible throughout the program
backend = {
    "load_drivers": io_mod.load_drivers,
    "load_requests": io_mod.load_requests,
    "generate_drivers": io_mod.generate_drivers,
    "generate_requests": io_mod.generate_requests,
    "init_state": sim_mod.init_state,
    "simulate_step": sim_mod.simulate_step
}