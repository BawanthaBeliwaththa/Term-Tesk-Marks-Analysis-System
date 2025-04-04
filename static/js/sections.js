$(document).ready(function(){
	$('#addSection').click(function(){
		$('#sectionModal').modal('show');
		$('#sectionForm')[0].reset();		
		$('.modal-title').html("<i class='fa fa-plus'></i> Add SEction");
		$('#action').val('addSection');
		$('#save').val('Save');
	});	
});