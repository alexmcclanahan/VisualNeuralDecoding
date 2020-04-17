
import os
from allensdk.brain_observatory.ecephys.ecephys_session import EcephysSession
from allensdk.brain_observatory.ecephys.ecephys_project_cache import EcephysProjectCache
import matplotlib.pyplot as plt
from allensdk.brain_observatory.ecephys.visualization import plot_mean_waveforms, plot_spike_counts, raster_plot

data_dir = '/Users/bioel/PycharmProjects/untitled4/ecephys_cache_dir'
manifest_path = os.path.join(data_dir, 'manifest.json')
cache = EcephysProjectCache.from_warehouse(manifest = manifest_path)
session = cache.get_session_data(session_id=715093703)
units_with_very_high_snr = session.units[session.units['snr'] > 1.0].head(7)
high_snr_unit_ids = units_with_very_high_snr.index.values


drifting_gratings_presentation_ids = session.stimulus_presentations.loc[
    (session.stimulus_presentations['stimulus_name'] == 'natural_scenes')
].index.values

times = session.presentationwise_spike_times(
    stimulus_presentation_ids=drifting_gratings_presentation_ids,
    unit_ids=high_snr_unit_ids
)

first_drifting_grating_presentation_id = times['stimulus_presentation_id'].values[0]
plot_times = times[times['stimulus_presentation_id'] == first_drifting_grating_presentation_id]

fig = raster_plot(plot_times)
plt.show()
