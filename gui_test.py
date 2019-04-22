import sys  
if sys.version_info[0] >= 3:  
    import PySimpleGUI as sg  
else:  
    import PySimpleGUI27 as sg  

layout = [[sg.Text('Your typed chars appear here:'), sg.Text('', key='_OUTPUT_') ],  
          [sg.Text('Query'), sg.Input(do_not_clear=True, key='_QUERY_')],
          [sg.Text('Category'), sg.Listbox(values=('Warehouse/Storage Facility', 
                                                   'Commercial Food Distribution Center', 
                                                   'Farm/Ranch',
                                                   'Food Distribution',
                                                   'Food Production Center',
                                                   'Food Retail',
                                                   'Grain Storage',
                                                   'Generation Station', 
                                                   'Natural Gas Facility',
                                                   'Petroleum Facility',
                                                   'Propane Facility',
                                                   'Government Site Infrastructure',
                                                   'Medical Treatment Facility (Hospital)',
                                                   'Civilian Television'), key='_CATEGORY_',
                                                   size=(30, 3))],
          [sg.Text('Max number of results'), sg.Slider(range=(1, 20), orientation='h', size=(20, 20), default_value=10, key='_RESULTS_')],
          [sg.Button('Submit'), sg.Button('Exit')]]  

window = sg.Window('Window Title').Layout(layout)  

while True:                 # Event Loop  
  event, values = window.Read()  
  print(event, values)
  if event is None or event == 'Exit':  
      break  
  if event == 'Submit':  
      # change the "output" element to be the value of "input" element  
      window.FindElement('_OUTPUT_').Update(values['_QUERY_'])

window.Close()