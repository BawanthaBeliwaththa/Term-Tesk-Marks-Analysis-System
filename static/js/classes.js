$(document).ready(function(){
	$('#addClass').click(function(){
		$('#classModal').modal('show');
		$('#classForm')[0].reset();		
		$('.modal-title').html("<i class='fa fa-plus'></i> Add Class");
		$('#action').val('addClass');
		$('#save').val('Add Class');
	});		
});