import matplotlib.pyplot as plt
import logging

def plot_tracks_mask_field_loop(track,field,Mask,axes=None,name=None,plot_dir='./',figsize=(10,10),**kwargs):
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import os
    time=field.coord('time')
    if name is None:
        name=field.name()
    for i in range(len(time.points)):
        fig1,ax1=plt.subplots(ncols=1, nrows=1,figsize=figsize, subplot_kw={'projection': ccrs.PlateCarree()})
        datestring_file=time.units.num2date(time.points[i]).strftime('%Y-%m-%d_%H:%M:%S')
        ax1=plot_tracks_mask_field(track[track['frame']==i],field[i],Mask[i],axes=ax1,**kwargs)
        savepath_png=os.path.join(plot_dir,name+'_'+datestring_file+'.png')
        fig1.savefig(savepath_png,dpi=600)
        logging.debug('Figure '+str(i) + ' plotted to ' + str(savepath_png))

        plt.close()
    plt.close() 


def plot_tracks_mask_field(track,field,Mask,axes=None,axis_extent=None,
                           plot_outline=True,plot_marker=True,marker_track='x',plot_number=True,
                           vmin=None,vmax=None,n_levels=50,orientation_colorbar='horizontal',pad_colorbar=0.2):
    import cartopy
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    import iris.plot as iplt
    from matplotlib.ticker import MaxNLocator
    import cartopy.feature as cfeature
    import numpy as np
    from cloudtrack import mask_particle,mask_particle_surface
    from matplotlib import ticker
    
    if type(axes) is not cartopy.mpl.geoaxes.GeoAxesSubplot:
        raise ValueError('axes had to be cartopy.mpl.geoaxes.GeoAxesSubplot')

    
    datestring=field.coord('time').units.num2date(field.coord('time').points[0]).strftime('%Y-%m-%d %H:%M:%S')

    axes.set_title(datestring)
    
    gl = axes.gridlines(draw_labels=True)
    majorLocator = MaxNLocator(nbins=5,steps=[1,2,5,10])
    gl.xlocator=majorLocator
    gl.ylocator=majorLocator
    gl.xformatter = LONGITUDE_FORMATTER
    axes.tick_params(axis='both', which='major', labelsize=6)
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabels_top = False
    gl.ylabels_right = False
    axes.coastlines('10m')    
    #    rivers=cfeature.NaturalEarthFeature(category='physical', name='rivers_lake_centerlines',scale='10m',facecolor='none')
    lakes=cfeature.NaturalEarthFeature(category='physical', name='lakes',scale='10m',facecolor='none')
    axes.add_feature(lakes, edgecolor='black')
    axes.set_xlabel('longitude')
    axes.set_ylabel('latitude')  


    axes.set_extent(axis_extent)
    
    plot_field=iplt.contourf(field,coords=['longitude','latitude'],
                        levels=np.linspace(vmin,vmax,num=n_levels),axes=axes,cmap='viridis',vmin=vmin,vmax=vmax)
    
    colors_mask=['darkred','orange','crimson','red','darkorange']
    
    for i_row,row in track.iterrows():
        if 'particle' in row:
            particle=row['particle']
            color=colors_mask[int(particle%len(colors_mask))]
        
            if plot_number:        
                particle_string='     '+str(int(row['particle']))
                axes.text(row['longitude'],row['latitude'],particle_string,color=color,fontsize=6)
            if plot_outline:
                Mask_i=None
                if Mask.ndim==2:
                    Mask_i=mask_particle(Mask,particle,masked=False)
                elif Mask.ndim==3:
                    Mask_i=mask_particle_surface(Mask,particle,masked=False,z_coord='model_level_number')
                else:
                    raise ValueError('mask has shape that cannot be understood')
                    
                iplt.contour(Mask_i,coords=['longitude','latitude'],
                             levels=[0,particle],colors=color,axes=axes)

        else:
            color=colors_mask[0]
        
        if plot_marker:
            axes.plot(row['longitude'],row['latitude'],color=color,marker=marker_track)


    cbar=plt.colorbar(plot_field,orientation=orientation_colorbar, pad=pad_colorbar)
    cbar.ax.set_xlabel(field.name()+ '('+field.units.symbol +')') 
    tick_locator = ticker.MaxNLocator(nbins=5)
    cbar.locator = tick_locator
    cbar.update_ticks()
    
    return axes

def plot_mask_cell_track_follow(particle,track, cog, features, mask_total,
                                    w_max, TWP, width=10000,
                                    name= 'test', plotdir='./',
                                    n_core=1,file_format=['png'],**kwargs):
        from iris import Constraint
        from numpy import unique
        import os
        track_cell=track[track['particle']==particle]
        for i_row,row in track_cell.iterrows():
            
            constraint_time = Constraint(time=row['time'])
            constraint_x = Constraint(projection_x_coordinate = lambda cell: row['projection_x_coordinate']-width < cell < row['projection_x_coordinate']+width)
            constraint_y = Constraint(projection_y_coordinate = lambda cell: row['projection_y_coordinate']-width < cell < row['projection_y_coordinate']+width)
            constraint = constraint_time & constraint_x & constraint_y
            mask_total_i=mask_total.extract(constraint)
            if w_max is None:
                w_max_i=None
            else:
                w_max_i=w_max.extract(constraint)
            if TWP is None:
                TWP_i=None
            else:
                TWP_i=TWP.extract(constraint)

            cells=list(unique(mask_total_i.core_data()))
            if particle not in cells:
                cells.append(particle)
            cells.remove(0)
            track_i=track[track['particle'].isin(cells)]
            track_i=track_i[track_i['time']==row['time']]
            if cog is None:
               cog_i=None
            else:
                cog_i=cog[cog['particle'].isin(cells)]
                cog_i=cog_i[cog_i['time']==row['time']]
                
            if features is None:
                features_i=None
            else:
                features_i=features[features['time']==row['time']]


            fig1, ax1 = plt.subplots(ncols=1, nrows=1, figsize=(10/2.54, 10/2.54))
            fig1.subplots_adjust(left=0.2, bottom=0.15, right=0.85, top=0.85)
            
            datestring = row['time'].strftime('%Y-%m-%d %H:%M:%S')

            ax1=plot_mask_cell_individual_follow(particle_i=particle,track=track_i, cog=cog_i,features=features_i,
                                           mask_total=mask_total_i,
                                           w_max=w_max_i, TWP=TWP_i,
                                           width=width,
                                           axes=ax1,**kwargs)
                   
            out_dir = os.path.join(plotdir, name)
            os.makedirs(out_dir, exist_ok=True)
            if 'png' in file_format:
                savepath_png = os.path.join(out_dir, name  + '_' + datestring + '.png')
                fig1.savefig(savepath_png, dpi=600)
                logging.debug('w_max TWP Mask plot saved to ' + savepath_png)
            if 'pdf' in file_format:
                savepath_pdf = os.path.join(out_dir, name  + '_' + datestring + '.pdf')
                fig1.savefig(savepath_pdf, dpi=600)
                logging.debug('w_max TWP Mask plot saved to ' + savepath_pdf)
            plt.close()
            plt.clf()


def plot_mask_cell_individual_follow(particle_i,track, cog,features, mask_total,
                               w_max, TWP, width=10000,
                               axes=plt.gca(),
                               vmin_w_max=0,vmax_w_max=50,levels_w_max=None,
                               contour_labels=False,
                               vmin_TWP=0,vmax_TWP=100,levels_TWP=None
                               ):   
    import numpy as np
    from cloudtrack.watershedding  import mask_particle_surface
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    from matplotlib.colors import Normalize
    
    
    divider = make_axes_locatable(axes)
    
    x_pos=track[track['particle']==particle_i]['projection_x_coordinate'].item()
    y_pos=track[track['particle']==particle_i]['projection_y_coordinate'].item()
    if TWP is not None:
        if levels_TWP is None:
            levels_TWP=np.linspace(vmin_TWP,vmax_TWP, 10)
        plot_TWP = axes.contourf((TWP.coord('projection_x_coordinate').points-x_pos)/1000,
                                 (TWP.coord('projection_y_coordinate').points-y_pos)/1000,
                                 TWP.data,
                                 levels=levels_TWP, cmap='Blues', vmin=vmin_TWP, vmax=vmax_TWP)    
        
        
        cax1 = divider.append_axes("right", size="5%", pad=0.1)
        norm1= Normalize(vmin=vmin_TWP, vmax=vmax_TWP)
        sm1= plt.cm.ScalarMappable(norm=norm1, cmap = plot_TWP.cmap)
        sm1.set_array([])
        
        cbar_TWP = plt.colorbar(sm1, orientation='vertical',cax=cax1)
        cbar_TWP.ax.set_ylabel('TWP (kg/m$^2$)')
        cbar_TWP.set_clim(vmin_TWP, vmax_TWP)

    if w_max is not None:
        if levels_w_max is None:
            levels_w_max=np.linspace(vmin_w_max, vmax_w_max, 5)
        plot_w_max = axes.contour((w_max.coord('projection_x_coordinate').points-x_pos)/1000,
                                  (w_max.coord('projection_y_coordinate').points-y_pos)/1000,
                                  w_max.data,
                                  cmap='summer',
                                  levels=levels_w_max,vmin=vmin_w_max, vmax=vmax_w_max,
                                  linewidths=0.8)
        
        if contour_labels:
            axes.clabel(plot_w_max, fontsize=10)
    
        cax2 = divider.append_axes("bottom", size="5%", pad=0.1)
        norm2= Normalize(vmin=vmin_w_max, vmax=vmax_w_max)
        sm2= plt.cm.ScalarMappable(norm=norm2, cmap = plot_w_max.cmap)
        sm2.set_array([])
        cbar_w = plt.colorbar(sm2, orientation='horizontal',cax=cax2)
        cbar_w.ax.set_xlabel('w_max (m/s)')
        cbar_w.set_clim(vmin_w_max, vmax_w_max)


    
#    colors_mask = ['pink','darkred', 'orange', 'red', 'darkorange']
    for i_row, row in track.iterrows():
        particle = int(row['particle'])
        if particle==particle_i:
            color='darkred'
        else:
            color='darkorange'
#        color = colors_mask[int(particle % len(colors_mask))]
            
        particle_string='   '+str(int(row['particle']))
        axes.text((row['projection_x_coordinate']-x_pos)/1000,
                  (row['projection_y_coordinate']-y_pos)/1000,
                  particle_string,color=color,fontsize=6)

        # Plot marker for tracked cell centre as a cross
        axes.plot((row['projection_x_coordinate']-x_pos)/1000,
                  (row['projection_y_coordinate']-y_pos)/1000,
                  'x', color=color,markersize=4)
        
        
        #Create surface projection of mask for the respective cell and plot it in the right color
        z_coord = 'model_level_number'
        mask_total_i_surface = mask_particle_surface(mask_total, particle, masked=False, z_coord=z_coord)
        axes.contour((mask_total_i_surface.coord('projection_x_coordinate').points-x_pos)/1000,
                     (mask_total_i_surface.coord('projection_y_coordinate').points-y_pos)/1000,
                     mask_total_i_surface.data, 
                     levels=[0, particle], colors=color, linestyles=':',linewidth=1)

    if cog is not None:

        for i_row, row in cog.iterrows():
            particle = row['particle']
            
            if particle==particle_i:
                color='darkred'
            else:
                color='darkorange'
            # plot marker for centre of gravity as a circle    
            axes.plot((row['x_M']-x_pos)/1000, (row['y_M']-y_pos)/1000,
                      'o', markeredgecolor=color, markerfacecolor='None',markersize=4)
    
    if features is not None:

        for i_row, row in features.iterrows():
            color='purple'
            axes.plot((row['projection_x_coordinate']-x_pos)/1000,
                      (row['projection_y_coordinate']-y_pos)/1000,
                      '+', color=color,markersize=3)

    axes.set_xlabel('x (km)')
    axes.set_ylabel('y (km)')        
    axes.set_xlim([-1*width/1000, width/1000])
    axes.set_ylim([-1*width/1000, width/1000])
    axes.xaxis.set_label_position('top') 
    axes.xaxis.set_ticks_position('top')
 
    return axes

def plot_mask_cell_track_static(particle,track, cog, features, mask_total,
                                    w_max, TWP, width=10000,
                                    name= 'test', plotdir='./',
                                    n_core=1,file_format=['png'],**kwargs):
        from iris import Constraint
        from numpy import unique
        import os
        track_cell=track[track['particle']==particle]
        x_min=track_cell['projection_x_coordinate'].min()-width
        x_max=track_cell['projection_x_coordinate'].max()+width
        y_min=track_cell['projection_y_coordinate'].min()-width
        y_max=track_cell['projection_y_coordinate'].max()+width
        
        for i_row,row in track_cell.iterrows():
            
            constraint_time = Constraint(time=row['time'])
            constraint_x = Constraint(projection_x_coordinate = lambda cell: x_min < cell < x_max)
            constraint_y = Constraint(projection_y_coordinate = lambda cell: y_min < cell < y_max)
            constraint = constraint_time & constraint_x & constraint_y
            mask_total_i=mask_total.extract(constraint)
            if w_max is None:
                w_max_i=None
            else:
                w_max_i=w_max.extract(constraint)
            if TWP is None:
                TWP_i=None
            else:
                TWP_i=TWP.extract(constraint)

            cells=list(unique(mask_total_i.core_data()))
            if particle not in cells:
                cells.append(particle)
            cells.remove(0)
            track_i=track[track['particle'].isin(cells)]
            track_i=track_i[track_i['time']==row['time']]
            
            if cog is None:
                cog_i=None
            else:
                cog_i=cog[cog['particle'].isin(cells)]
                cog_i=cog_i[cog_i['time']==row['time']]

            if features is None:
                features_i=None
            else:
                features_i=features[features['time']==row['time']]


            fig1, ax1 = plt.subplots(ncols=1, nrows=1, figsize=(10/2.54, 10/2.54))
            fig1.subplots_adjust(left=0.2, bottom=0.15, right=0.85, top=0.85)
            
            datestring = row['time'].strftime('%Y-%m-%d %H:%M:%S')

            ax1=plot_mask_cell_individual_static(particle_i=particle,
                                                 track=track_i, cog=cog_i,features=features_i, 
                                                 mask_total=mask_total_i,
                                                 w_max=w_max_i, TWP=TWP_i,
                                                 xlim=[x_min/1000,x_max/1000],ylim=[y_min/1000,y_max/1000],
                                                 axes=ax1,**kwargs)
                   
            out_dir = os.path.join(plotdir, name)
            os.makedirs(out_dir, exist_ok=True)
            if 'png' in file_format:
                savepath_png = os.path.join(out_dir, name  + '_' + datestring + '.png')
                fig1.savefig(savepath_png, dpi=600)
                logging.debug('w_max TWP Mask plot saved to ' + savepath_png)
            if 'pdf' in file_format:
                savepath_pdf = os.path.join(out_dir, name  + '_' + datestring + '.pdf')
                fig1.savefig(savepath_pdf, dpi=600)
                logging.debug('w_max TWP Mask plot saved to ' + savepath_pdf)
            plt.close()
            plt.clf()


def plot_mask_cell_individual_static(particle_i,track, cog, features, mask_total,
                               w_max, TWP,
                               axes=plt.gca(),xlim=None,ylim=None,
                               vmin_w_max=0,vmax_w_max=50,levels_w_max=None,
                               contour_labels=False,
                               vmin_TWP=0,vmax_TWP=100,levels_TWP=None
                               ):   
    import numpy as np
    from cloudtrack.watershedding  import mask_particle_surface
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    from matplotlib.colors import Normalize
    
    
    divider = make_axes_locatable(axes)
    
    if TWP is not None:
        if levels_TWP is None:
            levels_TWP=np.linspace(vmin_TWP,vmax_TWP, 10)
        plot_TWP = axes.contourf(TWP.coord('projection_x_coordinate').points/1000,
                                 TWP.coord('projection_y_coordinate').points/1000,
                                 TWP.data,
                                 levels=levels_TWP, cmap='Blues', vmin=vmin_TWP, vmax=vmax_TWP)    
        
        
        cax1 = divider.append_axes("right", size="5%", pad=0.1)
        norm1= Normalize(vmin=vmin_TWP, vmax=vmax_TWP)
        sm1= plt.cm.ScalarMappable(norm=norm1, cmap = plot_TWP.cmap)
        sm1.set_array([])
        
        cbar_TWP = plt.colorbar(sm1, orientation='vertical',cax=cax1)
        cbar_TWP.ax.set_ylabel('TWP (kg/m$^2$)')
        cbar_TWP.set_clim(vmin_TWP, vmax_TWP)

    if w_max is not None:
        if levels_w_max is None:
            levels_w_max=np.linspace(vmin_w_max, vmax_w_max, 5)
        plot_w_max = axes.contour(w_max.coord('projection_x_coordinate').points/1000,
                                  w_max.coord('projection_y_coordinate').points/1000,
                                  w_max.data,
                                  cmap='summer',
                                  levels=levels_w_max,vmin=vmin_w_max, vmax=vmax_w_max,
                                  linewidths=0.8)
        
        if contour_labels:
            axes.clabel(plot_w_max, fontsize=10)
    
        cax2 = divider.append_axes("bottom", size="5%", pad=0.1)
        norm2= Normalize(vmin=vmin_w_max, vmax=vmax_w_max)
        sm2= plt.cm.ScalarMappable(norm=norm2, cmap = plot_w_max.cmap)
        sm2.set_array([])
        cbar_w = plt.colorbar(sm2, orientation='horizontal',cax=cax2)
        cbar_w.ax.set_xlabel('w_max (m/s)')
        cbar_w.set_clim(vmin_w_max, vmax_w_max)


    
#    colors_mask = ['pink','darkred', 'orange', 'red', 'darkorange']
    for i_row, row in track.iterrows():
        particle = int(row['particle'])
        if particle==particle_i:
            color='darkred'
        else:
            color='darkorange'
#        color = colors_mask[int(particle % len(colors_mask))]
            
        particle_string='   '+str(int(row['particle']))
        axes.text(row['projection_x_coordinate']/1000,
                  row['projection_y_coordinate']/1000,
                  particle_string,color=color,fontsize=6)

        # Plot marker for tracked cell centre as a cross
        axes.plot(row['projection_x_coordinate']/1000,
                  row['projection_y_coordinate']/1000,
                  'x', color=color,markersize=4)
        
        
        #Create surface projection of mask for the respective cell and plot it in the right color
        z_coord = 'model_level_number'
        mask_total_i_surface = mask_particle_surface(mask_total, particle, masked=False, z_coord=z_coord)
        axes.contour(mask_total_i_surface.coord('projection_x_coordinate').points/1000,
                     mask_total_i_surface.coord('projection_y_coordinate').points/1000,
                     mask_total_i_surface.data, 
                     levels=[0, particle], colors=color, linestyles=':',linewidth=1)
    if cog is not None:
    
        for i_row, row in cog.iterrows():
            particle = row['particle']
            
            if particle==particle_i:
                color='darkred'
            else:
                color='darkorange'
            # plot marker for centre of gravity as a circle    
            axes.plot(row['x_M']/1000, row['y_M']/1000,
                      'o', markeredgecolor=color, markerfacecolor='None',markersize=4)

    if features is not None:
    
        for i_row, row in features.iterrows():
            color='purple'
            axes.plot(row['projection_x_coordinate']/1000,
                      row['projection_y_coordinate']/1000,
                      '+', color=color,markersize=3)

    axes.set_xlabel('x (km)')
    axes.set_ylabel('y (km)')        
    axes.set_xlim(xlim)
    axes.set_ylim(ylim)
    axes.xaxis.set_label_position('top') 
    axes.xaxis.set_ticks_position('top')
 
    return axes