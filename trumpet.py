notes = [
  ["E3", "2-123"],
  ["F3", "2-13"],
  ["F#3", "2-23"],
  ["G3", "2-12"],
  ["Ab3", "2-1"],
  ["A3", "2-2"],
  ["Bb3", "2-"],
  ["B3", "3-123"],
  ["C4", "3-13"],
  ["C#4", "3-23"],
  ["D4", "3-12"],
  ["Eb4", "3-1"],
  ["E4", "3-2"],
  ["F4", "3-"],
  ["F#4", "4-23"],
  ["G4", "4-12"],
  ["Ab4", "4-1"],
  ["A4", "4-2"],
  ["Bb4", "4-"],
  ["B4", "5-12"],
  ["C5", "5-1"],
  ["C#5", "5-2"],
  ["D5", "5-"],
  ["Eb5", "6-1"],
  ["E5", "6-2"],
  ["F5", "6-"],
  ["F#5", "8-23"],
  ["G5", "8-12"],
  ["Ab5", "8-1"],
  ["A5", "8-2"],
  ["Bb5", "8-0"],
]

major = [2,2,1,2,2,2,1]

MAX_PARTIAL = 8
EQUAL_INTERVAL = 2**(1/12.0)

def parse_fingering(fingering_str):
  partial, fingers = fingering_str.split("-")
  return [int(partial), "1" in fingers, "2" in fingers, "3" in fingers]

# Turn our list into:
#   note_names: list of notes in order
#   notes_lookup_proper: hash from name to the name of the fingering
#   notes: hash from name to parsed fingering
note_names = [name for (name, fingering) in notes]
notes_lookup_proper = {}
for name, fingering in notes:
  notes_lookup_proper[name] = fingering
notes = {}
for name in note_names:
  notes[name] = parse_fingering(notes_lookup_proper[name])

class Trumpet(object):
  def __init__(
          self,
          tuning_slide=0,
          first_valve=(EQUAL_INTERVAL**2-1),
          second_valve=(EQUAL_INTERVAL-1),
          third_valve=(EQUAL_INTERVAL**3-1)):
    self.tuning_slide_ = tuning_slide
    self.first_valve_ = first_valve
    self.second_valve_ = second_valve
    self.third_valve_ = third_valve
    self.length_ = 1.0

  def __repr__(self):
    return "Trumpet(%0.4f, %0.4f, %0.4f, %0.4f)" % (
        self.tuning_slide_,
        self.first_valve_,
        self.second_valve_,
        self.third_valve_)

  def frequency(self, note):
    partial, first, second, third = notes[note]
    length = self.length_ + self.tuning_slide_
    if first:
      length += self.first_valve_
    if second:
      length += self.second_valve_
    if third:
      length += self.third_valve_
    wavelength = length / partial
    frequency = 1/wavelength

    return frequency

  def ideal_frequency(self, note):
    note_index = note_names.index(note)
    high_bb_index = note_names.index("Bb5")
    high_bb_frequency = 8.0
    delta = high_bb_index - note_index
    return high_bb_frequency / (EQUAL_INTERVAL**(delta))

  def error(self, note):
    return self.frequency(note)/self.ideal_frequency(note) - 1

  def msq_error_over(self, selected_notes):
    total_sq_error = 0
    for note in selected_notes:
      error = self.error(note)
      total_sq_error += (error*error)
    mean_sq_error = total_sq_error / len(selected_notes)
    return mean_sq_error**.5

def optimize(selected_notes):
  t = Trumpet()
  delta = 0.00005

  while True:
    adjacent_trumpets = [
      Trumpet(t.tuning_slide_ + delta, t.first_valve_, t.second_valve_, t.third_valve_),
      Trumpet(t.tuning_slide_ - delta, t.first_valve_, t.second_valve_, t.third_valve_),
      Trumpet(t.tuning_slide_, t.first_valve_ + delta, t.second_valve_, t.third_valve_),
      Trumpet(t.tuning_slide_, t.first_valve_ - delta, t.second_valve_, t.third_valve_),
      Trumpet(t.tuning_slide_, t.first_valve_, t.second_valve_ + delta, t.third_valve_),
      Trumpet(t.tuning_slide_, t.first_valve_, t.second_valve_ - delta, t.third_valve_),
      Trumpet(t.tuning_slide_, t.first_valve_, t.second_valve_, t.third_valve_ + delta),
      Trumpet(t.tuning_slide_, t.first_valve_, t.second_valve_, t.third_valve_ - delta),
    ]
    
    current_error = t.msq_error_over(selected_notes)
    
    best_adjacent_trumpet = None
    best_adjacent_trumpet_msqe = None
    for adjacent_trumpet in adjacent_trumpets:
      msqe = adjacent_trumpet.msq_error_over(selected_notes)
      if msqe < current_error:
        if best_adjacent_trumpet_msqe is None or msqe < best_adjacent_trumpet_msqe:
          best_adjacent_trumpet_msqe = msqe
          best_adjacent_trumpet = adjacent_trumpet
    
    if best_adjacent_trumpet is None:
      return t
    else:
      t = best_adjacent_trumpet

def print_status(t, selected_notes):
  for note in selected_notes:
    print "  %s\t%0.4f\t%.4f\t(%.2f%%)" % (note, t.ideal_frequency(note), t.frequency(note), t.error(note)*100)
  print
  print "  trumpet: ", repr(t)
  print
  print "  trumpet error:", t.msq_error_over(selected_notes)

def optimize_for_all_notes():
  t = optimize(note_names)
  print "untuned:"
  print_status(Trumpet(), note_names)
  print "tuned:"
  print_status(t, note_names)

def determine_best_key():
  generally_tuned = optimize(note_names)
  optimized_errors = []
  for i, note in enumerate(note_names[:12]):
    notes_without_numbers = []
    for interval in major:
      i += interval
      notes_without_numbers.append(note_names[i][:-1])
    all_notes = [key_note for key_note in note_names
                 if any(key_note[:-1] == x for x in notes_without_numbers)]
    low_enough_notes = [key_note for key_note in all_notes if notes[key_note][0] <= MAX_PARTIAL]
    t = optimize(low_enough_notes)
    #print note[:-1], generally_tuned.msq_error_over(low_enough_notes), t.msq_error_over(low_enough_notes)
    optimized_errors.append((t.msq_error_over(low_enough_notes), note[:-1], t))
  optimized_errors.sort()
  for error, note, t in optimized_errors:
    print "%.4f%%\t%s\t%r" % (error*100, note, t)
  print repr(Trumpet())


def start():
  determine_best_key()

if __name__ == "__main__":
  start()
