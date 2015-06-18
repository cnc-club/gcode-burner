#!/usr/bin/env python 
"""
Copyright (C) 2009 Nick Drobchenko, nick@cnc-club.ru
any help can be obtained at cnc-club.ru 
Russian forum: http://cnc-club.ru/forum/viewforum.php?f=15  
English forum: http://cnc-club.ru/forum/viewforum.php?f=33

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""



import getopt, sys, os, pygtk, gtk, re

class Burner: 
	def destroy(self, widget, data=None):
		gtk.main_quit()

	def usage():
		print "Usage is not ready yet. See help button inside gcode-burner." # TODO

	def help(self, widget):
		self.help_dialog = gtk.MessageDialog(self.window,
                                flags = gtk.DIALOG_DESTROY_WITH_PARENT,
                                 type=gtk.MESSAGE_INFO,
	                             buttons=gtk.BUTTONS_OK,
	                             message_format=None);
		f = open("gcode-burner.info", "r")
		self.help_dialog.set_markup(f.read())
		f.close()
		self.help_dialog.run()
		self.help_dialog.destroy()

#		g_signal_connect_swapped (dialog, "response",
 #                         G_CALLBACK (gtk_widget_destroy),
  #                        dialog);



	def set_image(self, widget=None):
		input_file =  self.input_file.get_filename() 
		if  input_file == None : 
			input_file = self.args_input_file
		
		if not os.path.isfile(input_file):
			message = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK, message_format=None)
			message.set_markup('Wrong file!')
			message.run()
			message.destroy()
			return
		try :
			self.pixbuf = gtk.gdk.pixbuf_new_from_file(input_file)			
		except :
			message = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_NONE, message_format=None)
			message.set_markup('Wrong image!')
			message.run()
			message.destroy()
			return
		self.img_w, self.img_h = self.pixbuf.get_width(), self.pixbuf.get_height()  
		if self.img_w==0 or self.img_h==0 : 
			print '(Wrong img)'
			return
		scale = float(self.config.get('Global','image-scale'))
		if self.img_w>self.img_h : scaled_buf = self.pixbuf.scale_simple(int(scale),int(scale*self.img_h/self.img_w),gtk.gdk.INTERP_BILINEAR)
		else :   scaled_buf = self.pixbuf.scale_simple(int(scale*self.img_w/self.img_h),int(scale),gtk.gdk.INTERP_BILINEAR)
		self.image.set_from_pixbuf(scaled_buf)
		self.set_hw()
		
	def set_hw(self):
		try: 
			self.w = self.spin_buttons["dots_x"].get_value()
			self.h = self.spin_buttons["dots_y"].get_value()
			if self.checkbuttons["aspect"].get_active(): 
				self.h = self.w/self.img_w*self.img_h
				self.spin_buttons["dots_y"].set_value(self.h)
		except: 
			pass		


	def generate_gcode(self, arg):
	
		output_file =  self.output_file.get_text() 
		if self.checkbuttons['save_to_file'].get_active():
			if self.checkbuttons['add_file_suffix'].get_active(): 
				d = os.path.dirname(output_file)
				l = os.listdir(d)
				name = os.path.split(output_file)[-1]
				name,ext = os.path.splitext(name)
				max_n = 0
				for s in l :
					r = re.match(r"^%s_0*(\d+)%s$"%(re.escape(name),re.escape(ext) ), s)
					if r :
						max_n = max(max_n,int(r.group(1)))
						
				
			output_file = d + "/" + name + "_%04d"%(max_n+1) + ext
			
			try :
				f = open(output_file,'w')	
			except:
				message = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_NONE, message_format=None)
				message.set_markup('Can not write to specified file! (%s)'%output_file)
				message.run()
				message.destroy()
				return
		

		self.scaled_pixbuf = self.pixbuf.scale_simple(int(self.w),int(self.h),gtk.gdk.INTERP_BILINEAR)
		pixels = self.scaled_pixbuf.get_pixels_array()

		zmin,zmax,ztr,x,y,x0,y0,feed = [self.spin_buttons[key].get_value() for key in 'z_min z_max z_traverse dot_width dot_height x_offset y_offset feed'.split()]
		header = self.header.get_text(self.header.get_start_iter(),self.header.get_end_iter())
		clean = self.clean_gcode.get_text(self.clean_gcode.get_start_iter(),self.clean_gcode.get_end_iter())
		clean_each = self.clean_each.get_text().lower()
		try :
			clean_v = float(clean_each)
		except :
			clean_v = None
		if 	clean_v <= 0 : clean_v = None
		v_sum = 0.	
		gcode = header
		
		parameterize = self.checkbuttons['paramtererization'].get_active() 
		if parameterize :
			gcode += """
			#<x-offset> = %s
			#<y-offset> = %s
			#<z-offset> = 0
			#<x-scale>  = 1
			#<y-scale>  = 1
			#<z-scale>  = 1
			#<z-traverse>  = %s
			#<feed>		= %s
			"""%(x0,y0,ztr,feed)
			gcode += '\n(Header end)\n' 
			gcode += 'G0 Z#<z-traverse>\n'
			gcode += 'G0 X#<x-offset> Y#<y-offset>\n' 
			gcode += 'G1 X#<x-offset> Y#<x-offset> F#<feed>\n'
		else: 
			gcode += '\n(Header end)\n' 
			gcode += 'G0 Z%f\n' %(ztr)  
			gcode += 'G0 X%f Y%f\n' %(x0, y0)  
			gcode += 'G1 X%f Y%f F%f\n' %(x0, y0, feed)  
			
		gcodel = []
		for j in range(len(pixels[0])):
			if 	"row" in clean_each :
				gcodel.append(clean+"\n")
			if self.checkbuttons['echo_filter_progress'].get_active():
				print "FILTER_PROGRESS=%d" % int(100*j/len(pixels[0]))
			for k in range(len(pixels)):
				# make zig-zag
				i = k if j%2==0 else len(pixels)-k-1
				#xy = j*rowstride+i*ch
				r = pixels[i][j][0]
				g = pixels[i][j][1]
				b = pixels[i][j][2]
				
				v = float(int(r)+int(g)+int(b))/255/3
				v_sum += 1.-v
				if clean_v!=None and v_sum > clean_v : 
					gcodel.append(clean+"\n")
					v_sum = 0
				if v!=0:
					depth = eval(self.z_func.get_text())
					if depth != None:
						if parameterize :
							gcodel.append( 'G0 X[%s*#<x-scale>+#<x-offset>] Y[%s*#<y-scale>+#<y-offset>]\n' %(x*i, y*j) ) 
							gcodel.append( 'G1 Z[%s*#<z-scale>+#<z-offset>]\n' % depth )
							gcodel.append( 'G0 Z#<z-traverse>\n' )
						else :
							gcodel.append( 'G0 X%f Y%f\n' %(x0+x*i, y0+y*j) ) 
							gcodel.append( 'G1 Z%f\n' % depth )
							gcodel.append( 'G0 Z%f\n' %(ztr) )
							
		gcode +="".join(gcodel) 		
		footer = self.footer.get_text(self.footer.get_start_iter(),self.footer.get_end_iter())
		gcode += '(Footer start)\n'+footer
	
		if self.checkbuttons['save_to_file'].get_active(): 
			f.write(gcode)
			f.close()
		else :
			print gcode

		if self.checkbuttons['save_options'].get_active():
			for key in self.spin_buttons :
				self.config.set('Spinners', key, self.spin_buttons[key].get_value())
			for key in self.checkbuttons:
				self.config.set('CheckButtons', key, 1 if self.checkbuttons[key].get_active() else 0)
			self.config.set('Global', 'header', header)
			self.config.set('Global', 'footer', footer)
			self.config.set('Global', 'clean-gcode', clean)
			
		input_file =  self.input_file.get_filename() 
		if  input_file == None : 
			input_file = self.args_input_file

		self.config.set('Global', 'input_file', input_file)	
		self.config.set('Global', 'output_file', self.output_file.get_text())

		self.config.set('Global', 'clean-each', self.clean_each.get_text())
		self.config.set('Global', 'z_func', self.z_func.get_text())
		
		f = open(self.ini_file,"w")
		self.config.write(f)			
		f.close()
		self.destroy(None,None)		
	
	def set_spinners(self):
		self.spin_buttons["dots_x"].set_value(self.w)			
		self.spin_buttons["dots_y"].set_value(self.h)		
		self.spin_buttons['dot_width'].set_value(self.spin_buttons["width"].get_value()/self.w) 
		self.spin_buttons['dot_height'].set_value(self.spin_buttons["height"].get_value()/self.h) 		

	def change_spinners(self, widget, key):
		if self.change_spinners_lock : return
		self.change_spinners_lock = True
		if key == 'dot_width': 
			self.spin_buttons['width'].set_value(self.w * self.spin_buttons[key].get_value()) 
		if key == 'width': 
			self.set_spinners()
		if key == 'dot_height': 
			self.spin_buttons['height'].set_value(self.h * self.spin_buttons[key].get_value()) 
		if key == 'height': 
			self.set_spinners()
		if key == 'dots_x': 
			self.w = self.spin_buttons[key].get_value()
			if self.checkbuttons["aspect"].get_active(): 
				self.h = self.w/self.img_w*self.img_h
			self.set_spinners()	
		if key == 'dots_y': 
			self.h = self.spin_buttons[key].get_value()
			if self.checkbuttons["aspect"].get_active(): 
				self.w = self.h/self.img_h*self.img_w
			self.set_spinners()
			
		if self.checkbuttons["aspect"].get_active():
			if key in ['dot_width', 'width'] :
				self.spin_buttons['height'	  ].set_value(self.spin_buttons['width'].get_value() * self.h / self.w)
				self.spin_buttons['dot_height'].set_value(float(self.spin_buttons['height'].get_value()) / self.h)
			else :
				self.spin_buttons['width'].set_value(self.spin_buttons['height'].get_value() * self.w / self.h)
				self.spin_buttons['dot_width'].set_value(float(self.spin_buttons['width'].get_value()) / self.w)
			
		self.change_spinners_lock = False


	def show_filename(self, widget):
		if widget.get_active():
			self.output_file.show()
		else:
			self.output_file.hide()
	
	def save_to_click(self, widget):
		self.output_file_dialog.set_filename(self.output_file.get_text())
		result = self.output_file_dialog.run()
		if result == gtk.RESPONSE_OK:
			self.output_file.set_text(self.output_file_dialog.get_filename())           
		self.output_file_dialog.hide()
		
	def __init__(self):
		self.change_spinners_lock = False
		self.ini_file = os.path.join( os.path.dirname(os.path.realpath(__file__)), "gcode-burner.ini" )
		
		import ConfigParser
		self.config = ConfigParser.RawConfigParser()
		self.config.read(self.ini_file)
		spinners = dict(self.config.items('Spinners'))

		field_names = dict(self.config.items('Field_names'))
		spinners_order =  self.config.get('Global','spinners_order').split()
		checkbuttons_order =  self.config.get('Global','checkbuttons_order').split()
		layout = self.config.get('Global','layout')

		try:
			opts, args = getopt.getopt(sys.argv[1:], "hi:", ["help", "input=" ])
		except getopt.GetoptError, err:
			# print help information and exit:
			print str(err) # will print something like "option -a not recognized"
			usage()
			sys.exit(2)
		input_file = None
		for o, a in opts:
			if o in ("-h", "--help"):
				usage()
				sys.exit()
			else:
				assert False, "unhandled option"

		if args == [] : 
			self.args_input_file = self.config.get('Global','input_file')
		else :		
			self.args_input_file = args[0]

		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.connect("destroy", self.destroy)
		table = gtk.Table(2+len(spinners_order) + len(checkbuttons_order)+1,4)

		i = 0 
		self.image = gtk.Image()
		if layout == "vertical" :	
			table.attach(self.image, 0, 3, 0, 1)
		else : 
			table.attach(self.image, 3, 4, 1, 2+len(spinners_order) + len(checkbuttons_order)+1)
		i += 1	

		self.input_file = gtk.FileChooserButton('Open image', backend=None)
		table.attach(self.input_file, 0, 2, i, i+1, xoptions=gtk.FILL)
		self.args_input_file = os.path.realpath(self.args_input_file)
		self.input_file.select_filename(self.args_input_file)
		self.input_file.connect("file-set", self.set_image)   
		self.set_image()
		i += 1	
		
		self.spin_buttons = {}

		self.z_func = gtk.Entry()
		self.z_func.set_text(self.config.get('Global','z_func'))
		table.attach(gtk.Label('Z function'), 0, 1, i, i+1)
		table.attach(self.z_func, 1, 2, i, i+1)
		i += 1

		for key in spinners_order:
			if key == '|':
				table.attach(gtk.HSeparator(), 0, 2, i, i+1, xoptions=gtk.FILL)
				i += 1
				continue
				
			adj = gtk.Adjustment(float(spinners[key]), -100000.0, 100000.0, 0.1, 100.0, 0.0)
			self.spin_buttons[key] = gtk.SpinButton(adjustment=adj, climb_rate=0.1, digits=5)
			table.attach(self.spin_buttons[key], 1, 2, i, i+1, xoptions=gtk.FILL)
			table.attach(gtk.Label(field_names[key]), 0, 1, i, i+1, xoptions=gtk.FILL)
			adj.connect("value_changed", self.change_spinners, key)
			i += 1

		self.set_hw()

		self.clean_each = gtk.Entry()
		self.clean_each.set_text(self.config.get('Global','clean-each'))
		table.attach(gtk.Label(self.config.get('Field_names','clean-each')), 0, 1, i, i+1)
		table.attach(self.clean_each, 1, 2, i, i+1)
		i += 1


		self.checkbuttons = {}
		j = 0
		for key in checkbuttons_order:
			self.checkbuttons[key] = gtk.CheckButton(field_names[key])
			self.checkbuttons[key].set_active( bool(int(self.config.get('CheckButtons',key))) )
			table.attach(self.checkbuttons[key], j, j+1, i, i+1, xoptions=gtk.FILL)
			j = (j+1)%2 
			if j==0 : 
				i += 1


		if j != 0 :			
			i += 1
		self.output_file = gtk.Entry()
		self.output_file.set_text(self.config.get('Global','output_file'))
		hbox = gtk.HBox()
		hbox.pack_start(self.output_file)
		self.output_file_dialog = gtk.FileChooserDialog(title='Save Gcode to',action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
		self.output_file_dialog.set_default_response(gtk.RESPONSE_OK)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_SAVE_AS,gtk.ICON_SIZE_BUTTON)
		self.save_to = gtk.Button(label=None)
		self.save_to.set_image(image)		
		hbox.pack_start(self.save_to, expand=False)
		self.save_to.connect("clicked", self.save_to_click)
		table.attach(hbox, 1, 3, i, i+1)


		self.checkbuttons['save_to_file'].connect("toggled",self.show_filename)
		table.attach(gtk.Label('File name'), 0, 1, i, i+1)

		i += 1		
	
		button = gtk.Button("Generate Gcode")
		table.attach(button, 2, 3, i, i+1)
		button.connect("clicked", self.generate_gcode)		

		button = gtk.Button("Help")
		table.attach(button, 0, 1, i, i+1)
		button.connect("clicked", self.help)		
		
		i += 1		

		frame = gtk.Frame('Header')
		textview = gtk.TextView()
		self.header = textview.get_buffer()
		self.header.set_text(self.config.get('Global','header'))
		textview.set_wrap_mode(gtk.WRAP_NONE)
		sw = gtk.ScrolledWindow()


		sw.set_size_request(250,150)
		frame.add(sw)
		sw.add(textview)
		table.attach(frame,2,3,1,7, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=5, ypadding=5 )


		frame = gtk.Frame('Footer')
		textview = gtk.TextView()
		self.footer = textview.get_buffer()
		self.footer.set_text(self.config.get('Global','footer'))
		textview.set_wrap_mode(gtk.WRAP_NONE)
		sw = gtk.ScrolledWindow()
		frame.add(sw)
		sw.add(textview)
		table.attach(frame,2,3,7,15, xoptions=gtk.EXPAND | gtk.FILL , yoptions=gtk.EXPAND | gtk.FILL, xpadding=5, ypadding=5 )


		frame = gtk.Frame('Clean Gcode')
		textview = gtk.TextView()
		self.clean_gcode = textview.get_buffer()
		self.clean_gcode.set_text(self.config.get('Global','clean-gcode'))
		textview.set_wrap_mode(gtk.WRAP_NONE)
		sw = gtk.ScrolledWindow()
		frame.add(sw)
		sw.add(textview)
		table.attach(frame,2,3,15,21, xoptions=gtk.EXPAND | gtk.FILL , yoptions=gtk.EXPAND | gtk.FILL, xpadding=5, ypadding=5 )
		
		self.window.add(table)
		self.window.show_all()		
		

def main():
	gtk.main()
	return 0	

if __name__ == "__main__":
	Burner()
	main()

